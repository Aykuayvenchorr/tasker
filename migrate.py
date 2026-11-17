import os
import io
import logging
import re
import sys
import traceback
from collections import defaultdict, deque

import psycopg2
from psycopg2 import sql

from dotenv import load_dotenv

load_dotenv(override=True)
# ============================================================
# SOURCE DATABASE
# ============================================================

# load_dotenv(override=True)

SOURCE_HOST = "spb99akl-pg01"
SOURCE_PORT = 5432
SOURCE_DATABASE = "datalake"
SOURCE_USER = ""
SOURCE_PASSWORD = ""
SOURCE_SCHEMA = "geo_umzr"


# ============================================================
# TARGET DATABASE
# ============================================================

TARGET_HOST = SOURCE_HOST
TARGET_PORT = SOURCE_PORT
TARGET_DATABASE = "bdgeo"
TARGET_USER = ""
TARGET_PASSWORD = ""
TARGET_SCHEMA = "geo_umzr"


RESET_TARGET_SCHEMA = True

# Проверки после миграции.
VERIFY_DATA = True
VERIFY_STRUCTURE = True
VERIFY_CONSTRAINTS = True


# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def log(message):
    logger.info(message)


# ============================================================
# ПОДКЛЮЧЕНИЕ
# ============================================================

def connect(host, port, database, user, password):
    log(f"Подключение к БД: {database}")

    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
    )
    
    # connection = psycopg2.connect(f"dbname={database} user='{user}' host={host} password='{password}'")

    connection.autocommit = False

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT current_database(), current_user
            """
        )
        database_name, user_name = cursor.fetchone()

    log(f"Подключено: БД={database_name}, пользователь={user_name}")

    return connection


# ============================================================
# ПРОВЕРКА ЦЕЛЕВОЙ СХЕМЫ
# ============================================================
# def check_target_schema(connection):
#     with connection.cursor() as cursor:

#         cursor.execute("""
#             SELECT
#                 current_database(),
#                 current_user,
#                 inet_server_addr(),
#                 inet_server_port();
#         """)

#         print("ПОДКЛЮЧЕНИЕ PYTHON:", cursor.fetchone())
#         print("TARGET_SCHEMA:", repr(TARGET_SCHEMA))

#         cursor.execute("""
#             SELECT schema_name
#             FROM information_schema.schemata
#             WHERE schema_name = 'geo_umzr';
#         """)

#         print("СХЕМА ИЗ PYTHON:", cursor.fetchall())

def check_target_schema(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.schemata
                WHERE schema_name = %s
            )
            """,
            (TARGET_SCHEMA,),
        )

        exists = cursor.fetchone()[0]

    if not exists:
        raise RuntimeError(
            f"Целевая схема '{TARGET_SCHEMA}' не существует. "
            "Создай её заранее."
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT has_schema_privilege(
                current_user,
                %s,
                'USAGE'
            ),
            has_schema_privilege(
                current_user,
                %s,
                'CREATE'
            )
            """,
            (TARGET_SCHEMA, TARGET_SCHEMA),
        )

        can_use, can_create = cursor.fetchone()

    if not can_use:
        raise PermissionError(
            f"Нет права USAGE на схему '{TARGET_SCHEMA}'."
        )

    if not can_create:
        raise PermissionError(
            f"Нет права CREATE на схему '{TARGET_SCHEMA}'."
        )

    log(
        f"Целевая схема '{TARGET_SCHEMA}' существует "
        "и доступна для создания объектов."
    )


# ============================================================
# ОЧИСТКА ЦЕЛЕВОЙ СХЕМЫ
# ============================================================

def reset_target_schema(connection):
    if not RESET_TARGET_SCHEMA:
        return

    log(f"Очистка целевой схемы '{TARGET_SCHEMA}'...")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                n.nspname,
                c.relname,
                c.relkind
            FROM pg_class c
            JOIN pg_namespace n
                ON n.oid = c.relnamespace
            WHERE n.nspname = %s
              AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
              AND c.relowner = (
                  SELECT oid
                  FROM pg_roles
                  WHERE rolname = current_user
              )
            ORDER BY c.relname
            """,
            (TARGET_SCHEMA,),
        )

        objects = cursor.fetchall()

    for schema_name, object_name, relkind in objects:
        if relkind == "r":
            object_type = "TABLE"
        elif relkind == "p":
            object_type = "TABLE"
        elif relkind == "v":
            object_type = "VIEW"
        elif relkind == "m":
            object_type = "MATERIALIZED VIEW"
        elif relkind == "f":
            object_type = "FOREIGN TABLE"
        else:
            continue

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP {} {} CASCADE").format(
                    sql.SQL(object_type),
                    sql.Identifier(schema_name, object_name),
                )
            )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT sequence_name
            FROM information_schema.sequences
            WHERE sequence_schema = %s
            """,
            (TARGET_SCHEMA,),
        )

        sequences = [row[0] for row in cursor.fetchall()]

    for sequence_name in sequences:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP SEQUENCE {} CASCADE").format(
                    sql.Identifier(TARGET_SCHEMA, sequence_name)
                )
            )

    connection.commit()

    log("Целевая схема очищена.")


# ============================================================
# ТАБЛИЦЫ
# ============================================================

def get_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.relname,
                c.relkind
            FROM pg_class c
            JOIN pg_namespace n
                ON n.oid = c.relnamespace
            WHERE n.nspname = %s
              AND c.relkind IN ('r', 'p')
              AND NOT c.relispartition
            ORDER BY c.relname
            """,
            (SOURCE_SCHEMA,),
        )

        return cursor.fetchall()


def get_columns(connection, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.attname,
                format_type(a.atttypid, a.atttypmod),
                pg_get_expr(ad.adbin, ad.adrelid),
                a.attnotnull,
                a.attidentity,
                a.attgenerated,
                CASE
                    WHEN a.attgenerated = 's'
                    THEN pg_get_expr(ad.adbin, ad.adrelid)
                    ELSE NULL
                END AS generated_expression
            FROM pg_attribute a
            JOIN pg_class c
                ON c.oid = a.attrelid
            JOIN pg_namespace n
                ON n.oid = c.relnamespace
            LEFT JOIN pg_attrdef ad
                ON ad.adrelid = a.attrelid
                AND ad.adnum = a.attnum
            WHERE n.nspname = %s
              AND c.relname = %s
              AND a.attnum > 0
              AND NOT a.attisdropped
            ORDER BY a.attnum
            """,
            (SOURCE_SCHEMA, table_name),
        )

        return cursor.fetchall()


# ============================================================
# ВСПОМОГАТЕЛЬНАЯ ЗАМЕНА СХЕМЫ
# ============================================================

def replace_schema(expression):
    if not expression:
        return expression

    result = expression

    result = result.replace(
        f'"{SOURCE_SCHEMA}".',
        f'"{TARGET_SCHEMA}".',
    )

    if SOURCE_SCHEMA != TARGET_SCHEMA:
        pattern = rf"(?<![\w\"]){re.escape(SOURCE_SCHEMA)}\."
        result = re.sub(
            pattern,
            f"{TARGET_SCHEMA}.",
            result,
        )

    return result


# ============================================================
# SEQUENCES
# ============================================================

def get_sequences(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.relname AS sequence_name,
                format_type(s.seqtypid, NULL) AS data_type,
                s.seqstart,
                s.seqmin,
                s.seqmax,
                s.seqincrement,
                s.seqcycle,
                s.seqcache
            FROM pg_sequence s
            JOIN pg_class c
                ON c.oid = s.seqrelid
            JOIN pg_namespace n
                ON n.oid = c.relnamespace
            WHERE n.nspname = %s
            ORDER BY c.relname
            """,
            (SOURCE_SCHEMA,),
        )

        return cursor.fetchall()


def get_identity_sequences(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT
                seq.relname
            FROM pg_class seq
            JOIN pg_namespace seq_ns
                ON seq_ns.oid = seq.relnamespace
            JOIN pg_depend dep
                ON dep.objid = seq.oid
            JOIN pg_class tbl
                ON tbl.oid = dep.refobjid
            JOIN pg_namespace tbl_ns
                ON tbl_ns.oid = tbl.relnamespace
            JOIN pg_attribute attr
                ON attr.attrelid = tbl.oid
                AND attr.attnum = dep.refobjsubid
            WHERE seq_ns.nspname = %s
              AND seq.relkind = 'S'
              AND dep.deptype = 'i'
              AND attr.attidentity IN ('a', 'd')
            """,
            (SOURCE_SCHEMA,),
        )

        return {row[0] for row in cursor.fetchall()}


def create_non_identity_sequences(
    source_connection,
    target_connection,
):
    sequences = get_sequences(source_connection)
    identity_sequences = get_identity_sequences(source_connection)

    log("Создание обычных sequences...")

    for sequence in sequences:
        (
            sequence_name,
            data_type,
            start_value,
            min_value,
            max_value,
            increment,
            cycle,
            cache,
        ) = sequence

        if sequence_name in identity_sequences:
            continue

        cycle_sql = "CYCLE" if cycle else "NO CYCLE"

        with target_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    CREATE SEQUENCE {}.{}
                    AS {}
                    INCREMENT BY {}
                    MINVALUE {}
                    MAXVALUE {}
                    START WITH {}
                    CACHE {}
                    {}
                    """
                ).format(
                    sql.Identifier(TARGET_SCHEMA),
                    sql.Identifier(sequence_name),
                    sql.SQL(data_type),
                    sql.Literal(increment),
                    sql.Literal(min_value),
                    sql.Literal(max_value),
                    sql.Literal(start_value),
                    sql.Literal(cache),
                    sql.SQL(cycle_sql),
                )
            )

    target_connection.commit()

    log("Обычные sequences созданы.")


def get_sequence_states(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.relname,
                s.last_value,
                s.is_called
            FROM pg_class c
            JOIN pg_namespace n
                ON n.oid = c.relnamespace
            JOIN pg_sequences ps
                ON ps.schemaname = n.nspname
                AND ps.sequencename = c.relname
            JOIN LATERAL (
                SELECT *
                FROM pg_catalog.pg_sequences
                WHERE schemaname = n.nspname
                  AND sequencename = c.relname
            ) dummy
                ON TRUE
            JOIN LATERAL (
                SELECT
                    last_value,
                    is_called
                FROM pg_catalog.pg_sequence
                WHERE seqrelid = c.oid
            ) s
                ON TRUE
            WHERE n.nspname = %s
            """,
            (SOURCE_SCHEMA,),
        )

        rows = cursor.fetchall()

    result = {}

    for sequence_name, last_value, is_called in rows:
        result[sequence_name] = (last_value, is_called)

    return result


def get_sequence_values(connection):
    sequences = get_sequences(connection)
    result = {}

    for sequence in sequences:
        sequence_name = sequence[0]

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "SELECT last_value, is_called "
                    "FROM {}.{}"
                ).format(
                    sql.Identifier(SOURCE_SCHEMA),
                    sql.Identifier(sequence_name),
                )
            )

            result[sequence_name] = cursor.fetchone()

    return result


def get_target_sequence_names(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s
              AND c.relkind = 'S'
            """,
            (TARGET_SCHEMA,),
        )
        return {row[0] for row in cursor.fetchall()}


def restore_sequence_states(source_connection, target_connection):
    sequence_states = get_sequence_values(source_connection)
    target_sequences = get_target_sequence_names(target_connection)

    with target_connection.cursor() as cursor:
        for source_sequence_name, (last_value, is_called) in sequence_states.items():
            target_sequence_name = source_sequence_name

            if target_sequence_name not in target_sequences:
                matches = [
                    name
                    for name in target_sequences
                    if name.lower() == source_sequence_name.lower()
                ]

                if len(matches) == 1:
                    target_sequence_name = matches[0]
                else:
                    log(
                        f"Sequence {source_sequence_name} не найдена "
                        f"в target — пропуск."
                    )
                    continue

            qualified_sequence = (
                f'"{TARGET_SCHEMA.replace(chr(34), chr(34) * 2)}".'
                f'"{target_sequence_name.replace(chr(34), chr(34) * 2)}"'
            )

            cursor.execute(
                "SELECT setval(%s::regclass, %s, %s)",
                (
                    qualified_sequence,
                    last_value,
                    is_called,
                ),
            )


# ============================================================
# ЗАВИСИМОСТИ ТАБЛИЦ
# ============================================================

def get_foreign_key_dependencies(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                child.relname AS child_table,
                parent.relname AS parent_table
            FROM pg_constraint con
            JOIN pg_class child
                ON child.oid = con.conrelid
            JOIN pg_namespace child_ns
                ON child_ns.oid = child.relnamespace
            JOIN pg_class parent
                ON parent.oid = con.confrelid
            JOIN pg_namespace parent_ns
                ON parent_ns.oid = parent.relnamespace
            WHERE con.contype = 'f'
              AND child_ns.nspname = %s
              AND parent_ns.nspname = %s
            """,
            (SOURCE_SCHEMA, SOURCE_SCHEMA),
        )

        return cursor.fetchall()


def sort_tables_by_dependencies(tables, dependencies):
    table_names = [table[0] for table in tables]

    graph = defaultdict(set)
    in_degree = {table_name: 0 for table_name in table_names}

    for child_table, parent_table in dependencies:
        if child_table == parent_table:
            continue

        if child_table not in in_degree:
            continue

        if parent_table not in in_degree:
            continue

        if child_table not in graph[parent_table]:
            graph[parent_table].add(child_table)
            in_degree[child_table] += 1

    queue = deque(
        table_name
        for table_name in table_names
        if in_degree[table_name] == 0
    )

    result = []

    while queue:
        table_name = queue.popleft()
        result.append(table_name)

        for child_table in sorted(graph[table_name]):
            in_degree[child_table] -= 1

            if in_degree[child_table] == 0:
                queue.append(child_table)

    if len(result) != len(table_names):
        remaining = [
            table_name
            for table_name in table_names
            if table_name not in result
        ]

        log(
            "Обнаружен циклический FK. "
            "Оставшиеся таблицы будут созданы в исходном порядке: "
            f"{remaining}"
        )

        result.extend(remaining)

    return result


# ============================================================
# СОЗДАНИЕ ТАБЛИЦ
# ============================================================

def build_column_definition(column):
    (
        column_name,
        data_type,
        default_value,
        not_null,
        identity,
        generated,
        generated_expression,
    ) = column

    parts = [
        sql.Identifier(column_name),
        sql.SQL(data_type),
    ]

    if identity:
        if identity == "a":
            parts.append(
                sql.SQL("GENERATED ALWAYS AS IDENTITY")
            )
        elif identity == "d":
            parts.append(
                sql.SQL("GENERATED BY DEFAULT AS IDENTITY")
            )

    elif generated == "s":
        expression = replace_schema(generated_expression)

        parts.append(
            sql.SQL("GENERATED ALWAYS AS ({}) STORED").format(
                sql.SQL(expression)
            )
        )

    elif default_value:
        default_value = replace_schema(default_value)

        parts.append(
            sql.SQL("DEFAULT {}").format(
                sql.SQL(default_value)
            )
        )

    if not_null:
        parts.append(sql.SQL("NOT NULL"))

    return sql.SQL(" ").join(parts)


def create_table(
    source_connection,
    target_connection,
    table_name,
):
    columns = get_columns(source_connection, table_name)

    column_definitions = [
        build_column_definition(column)
        for column in columns
    ]

    query = sql.SQL(
        "CREATE TABLE {}.{} ({})"
    ).format(
        sql.Identifier(TARGET_SCHEMA),
        sql.Identifier(table_name),
        sql.SQL(", ").join(column_definitions),
    )

    with target_connection.cursor() as cursor:
        cursor.execute(query)

    target_connection.commit()

    log(f"Создана таблица: {table_name}")


def create_tables(
    source_connection,
    target_connection,
    ordered_tables,
):
    for table_name in ordered_tables:
        if table_name != 'test':
            create_table(
                source_connection,
                target_connection,
                table_name,
            )


# ============================================================
# ПЕРЕНОС ДАННЫХ
# ============================================================

def copy_table_data(
    source_connection,
    target_connection,
    table_name,
):
    log(f"Перенос данных: {table_name}")

    buffer = io.StringIO()

    with source_connection.cursor() as source_cursor:
        source_cursor.copy_expert(
            sql.SQL(
                "COPY {}.{} TO STDOUT WITH CSV"
            ).format(
                sql.Identifier(SOURCE_SCHEMA),
                sql.Identifier(table_name),
            ).as_string(source_connection),
            buffer,
        )

    buffer.seek(0)

    with target_connection.cursor() as target_cursor:
        target_cursor.copy_expert(
            sql.SQL(
                "COPY {}.{} FROM STDIN WITH CSV"
            ).format(
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(table_name),
            ).as_string(target_connection),
            buffer,
        )

    target_connection.commit()


def copy_all_data(
    source_connection,
    target_connection,
    ordered_tables,
):
    for table_name in ordered_tables:
        copy_table_data(
            source_connection,
            target_connection,
            table_name,
        )


# ============================================================
# CONSTRAINTS
# ============================================================

def get_constraints(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                con.conname,
                tbl.relname,
                con.contype,
                pg_get_constraintdef(con.oid, true)
            FROM pg_constraint con
            JOIN pg_class tbl
                ON tbl.oid = con.conrelid
            JOIN pg_namespace ns
                ON ns.oid = tbl.relnamespace
            WHERE ns.nspname = %s
              AND con.contype IN ('p', 'u', 'c', 'f')
            ORDER BY
                CASE con.contype
                    WHEN 'p' THEN 1
                    WHEN 'u' THEN 2
                    WHEN 'c' THEN 3
                    WHEN 'f' THEN 4
                END,
                tbl.relname,
                con.conname
            """,
            (SOURCE_SCHEMA,),
        )

        return cursor.fetchall()


def create_non_foreign_key_constraints(
    source_connection,
    target_connection,
):
    constraints = get_constraints(source_connection)

    for constraint_name, table_name, constraint_type, definition in constraints:
        if constraint_type == "f":
            continue

        definition = replace_schema(definition)

        with target_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "ALTER TABLE {}.{} "
                    "ADD CONSTRAINT {} {}"
                ).format(
                    sql.Identifier(TARGET_SCHEMA),
                    sql.Identifier(table_name),
                    sql.Identifier(constraint_name),
                    sql.SQL(definition),
                )
            )

    target_connection.commit()

    log("PK / UNIQUE / CHECK созданы.")


def create_foreign_keys(
    source_connection,
    target_connection,
):
    constraints = get_constraints(source_connection)

    for constraint_name, table_name, constraint_type, definition in constraints:
        if constraint_type != "f":
            continue

        definition = replace_schema(definition)

        with target_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "ALTER TABLE {}.{} "
                    "ADD CONSTRAINT {} {}"
                ).format(
                    sql.Identifier(TARGET_SCHEMA),
                    sql.Identifier(table_name),
                    sql.Identifier(constraint_name),
                    sql.SQL(definition),
                )
            )

    target_connection.commit()

    log("Foreign keys созданы.")


# ============================================================
# ИНДЕКСЫ
# ============================================================

def get_indexes(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                index.relname,
                table_.relname,
                pg_get_indexdef(index.oid)
            FROM pg_index idx
            JOIN pg_class index
                ON index.oid = idx.indexrelid
            JOIN pg_class table_
                ON table_.oid = idx.indrelid
            JOIN pg_namespace ns
                ON ns.oid = table_.relnamespace
            LEFT JOIN pg_constraint con
                ON con.conindid = index.oid
            WHERE ns.nspname = %s
              AND NOT idx.indisprimary
              AND con.oid IS NULL
            ORDER BY table_.relname, index.relname
            """,
            (SOURCE_SCHEMA,),
        )

        return cursor.fetchall()


def create_indexes(
    source_connection,
    target_connection,
):
    indexes = get_indexes(source_connection)

    for index_name, table_name, index_definition in indexes:
        index_definition = replace_schema(index_definition)

        with target_connection.cursor() as cursor:
            cursor.execute(sql.SQL(index_definition))

    target_connection.commit()

    log("Обычные индексы созданы.")


# ============================================================
# ПРИВЯЗКА SERIAL SEQUENCES К КОЛОНКАМ
# ============================================================

def get_sequence_ownership(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                seq.relname AS sequence_name,
                tbl.relname AS table_name,
                attr.attname AS column_name
            FROM pg_class seq
            JOIN pg_namespace seq_ns
                ON seq_ns.oid = seq.relnamespace
            JOIN pg_depend dep
                ON dep.objid = seq.oid
            JOIN pg_class tbl
                ON tbl.oid = dep.refobjid
            JOIN pg_namespace tbl_ns
                ON tbl_ns.oid = tbl.relnamespace
            JOIN pg_attribute attr
                ON attr.attrelid = tbl.oid
                AND attr.attnum = dep.refobjsubid
            WHERE seq.relkind = 'S'
              AND seq_ns.nspname = %s
              AND tbl_ns.nspname = %s
              AND dep.deptype = 'a'
            ORDER BY seq.relname
            """,
            (SOURCE_SCHEMA, SOURCE_SCHEMA),
        )

        return cursor.fetchall()


def restore_sequence_ownership(
    source_connection,
    target_connection,
):
    ownership = get_sequence_ownership(source_connection)

    for sequence_name, table_name, column_name in ownership:
        with target_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "ALTER SEQUENCE {}.{} OWNED BY {}.{}.{}"
                ).format(
                    sql.Identifier(TARGET_SCHEMA),
                    sql.Identifier(sequence_name),
                    sql.Identifier(TARGET_SCHEMA),
                    sql.Identifier(table_name),
                    sql.Identifier(column_name),
                )
            )

    target_connection.commit()

    log("Привязка sequences к колонкам восстановлена.")


# ============================================================
# ПРОВЕРКА
# ============================================================

def get_table_count(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            """,
            (SOURCE_SCHEMA,),
        )

        return cursor.fetchone()[0]


def get_target_table_count(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            """,
            (TARGET_SCHEMA,),
        )

        return cursor.fetchone()[0]


def get_row_count(connection, schema_name, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL(
                "SELECT count(*) FROM {}.{}"
            ).format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )
        )

        return cursor.fetchone()[0]


def verify_structure(
    source_connection,
    target_connection,
):
    source_tables = get_tables(source_connection)
    target_count = get_target_table_count(target_connection)

    if len(source_tables) != target_count:
        raise RuntimeError(
            "Количество таблиц не совпадает: "
            f"source={len(source_tables)}, "
            f"target={target_count}"
        )

    log(
        f"Проверка структуры: {len(source_tables)} таблиц — OK."
    )


def verify_data(
    source_connection,
    target_connection,
    tables,
):
    log("Проверка количества строк...")

    for table_name, _ in tables:
        source_count = get_row_count(
            source_connection,
            SOURCE_SCHEMA,
            table_name,
        )

        target_count = get_row_count(
            target_connection,
            TARGET_SCHEMA,
            table_name,
        )

        if source_count != target_count:
            raise RuntimeError(
                f"Таблица '{table_name}': "
                f"source={source_count}, "
                f"target={target_count}"
            )

    log("Количество строк во всех таблицах совпадает.")


def verify_constraints(
    source_connection,
    target_connection,
):
    with source_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)
            FROM pg_constraint con
            JOIN pg_class tbl
                ON tbl.oid = con.conrelid
            JOIN pg_namespace ns
                ON ns.oid = tbl.relnamespace
            WHERE ns.nspname = %s
              AND con.contype IN ('p', 'u', 'c', 'f')
            """,
            (SOURCE_SCHEMA,),
        )

        source_count = cursor.fetchone()[0]

    with target_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)
            FROM pg_constraint con
            JOIN pg_class tbl
                ON tbl.oid = con.conrelid
            JOIN pg_namespace ns
                ON ns.oid = tbl.relnamespace
            WHERE ns.nspname = %s
              AND con.contype IN ('p', 'u', 'c', 'f')
            """,
            (TARGET_SCHEMA,),
        )

        target_count = cursor.fetchone()[0]

    if source_count != target_count:
        raise RuntimeError(
            "Количество constraints не совпадает: "
            f"source={source_count}, "
            f"target={target_count}"
        )

    log(
        f"Проверка constraints: {source_count} — OK."
    )


def filter_existing_tables(source_connection, target_connection, tables):
    result = []

    for table_name, relkind in tables:
        with target_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_class c
                    JOIN pg_namespace n
                        ON n.oid = c.relnamespace
                    WHERE n.nspname = %s
                      AND c.relname = %s
                      AND c.relkind IN ('r', 'p')
                )
                """,
                (TARGET_SCHEMA, table_name),
            )

            exists = cursor.fetchone()[0]

        if exists:
            log(
                f"Пропуск таблицы '{table_name}': "
                "она уже существует в target."
            )
            continue

        result.append((table_name, relkind))

    return result

    
# ============================================================
# ОСНОВНАЯ МИГРАЦИЯ
# ============================================================

def migrate():
    source_connection = None
    target_connection = None

    # try:
    log("=" * 70)
    log("НАЧАЛО МИГРАЦИИ")
    log("=" * 70)

    source_connection = connect(
        SOURCE_HOST,
        SOURCE_PORT,
        SOURCE_DATABASE,
        SOURCE_USER,
        SOURCE_PASSWORD,
    )

    target_connection = connect(
        TARGET_HOST,
        TARGET_PORT,
        TARGET_DATABASE,
        TARGET_USER,
        TARGET_PASSWORD,
    )

    check_target_schema(target_connection)

    tables = get_tables(source_connection)

    if not tables:
        raise RuntimeError(
            f"В исходной схеме '{SOURCE_SCHEMA}' нет таблиц."
        )


    # tables = filter_existing_tables(source_connection, target_connection, tables)

    # if not tables:
    #     raise RuntimeError(
    #         "После исключения уже существующих таблиц не осталось таблиц для миграции."
    #     )
    
    log(
        f"В исходной схеме найдено таблиц: {len(tables)}"
    )

    dependencies = get_foreign_key_dependencies(
        source_connection
    )

    ordered_tables = sort_tables_by_dependencies(
        tables,
        dependencies,
    )

    log("Порядок создания таблиц:")

    for number, table_name in enumerate(ordered_tables, 1):
        log(f"{number}. {table_name}")

    reset_target_schema(target_connection)

    create_non_identity_sequences(
        source_connection,
        target_connection,
    )

    create_tables(
        source_connection,
        target_connection,
        ordered_tables,
    )

    copy_all_data(
        source_connection,
        target_connection,
        ordered_tables,
    )

    restore_sequence_ownership(
        source_connection,
        target_connection,
    )

    restore_sequence_states(
        source_connection,
        target_connection,
    )

    create_non_foreign_key_constraints(
        source_connection,
        target_connection,
    )

    create_foreign_keys(
        source_connection,
        target_connection,
    )

    create_indexes(
        source_connection,
        target_connection,
    )

    if VERIFY_STRUCTURE:
        verify_structure(
            source_connection,
            target_connection,
        )

    if VERIFY_DATA:
        verify_data(
            source_connection,
            target_connection,
            tables,
        )

    if VERIFY_CONSTRAINTS:
        verify_constraints(
            source_connection,
            target_connection,
        )

    log("=" * 70)
    log("МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
    log("=" * 70)

    # except Exception as exc:
    #     if target_connection:
    #         try:
    #             target_connection.rollback()
    #         except Exception:
    #             pass

    #     log("=" * 70)
    #     log("МИГРАЦИЯ ОСТАНОВЛЕНА С ОШИБКОЙ")
    #     log("=" * 70)
    #     log(f"Тип ошибки: {type(exc).__name__}")
    #     log(f"Ошибка: {exc}")

    #     traceback.print_exc()

    #     sys.exit(1)

    # finally:
    if source_connection:
        source_connection.close()

    if target_connection:
        target_connection.close()


if __name__ == "__main__":
    migrate()