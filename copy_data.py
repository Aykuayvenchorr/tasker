import io
import logging

import psycopg2
from psycopg2 import sql


# ============================================================
# НАСТРОЙКИ
# ============================================================

HOST = "spb99akl-pg01"
PORT = 5432

SOURCE_DB = "datalake"
TARGET_DB = "bdgeo"

USER = "Gorbunov.EAl"
PASSWORD = ""

SOURCE_SCHEMA = "geo_umzr"
TARGET_SCHEMA = "geo_umzr"

# ЭТУ ТАБЛИЦУ НЕ ТРОГАЕМ
EXCLUDED_TABLES = {"test"}


# ============================================================
# ЛОГИ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# ПОДКЛЮЧЕНИЕ
# ============================================================

def get_connection(database):
    return psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=database,
        user=USER,
        password=PASSWORD
    )


# ============================================================
# ТАБЛИЦЫ
# ============================================================

def get_tables(connection, schema):
    """
    Получает таблицы схемы.

    test исключается.
    """

    query = """
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n
            ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relkind IN ('r', 'p')
          AND c.relname <> ALL(%s)
        ORDER BY c.relname;
    """

    with connection.cursor() as cur:
        cur.execute(
            query,
            (schema, list(EXCLUDED_TABLES))
        )

        return [row[0] for row in cur.fetchall()]


# ============================================================
# КОЛОНКИ
# ============================================================

def get_columns(connection, schema, table):
    """
    Получает список колонок в порядке их расположения.
    """

    query = """
        SELECT a.attname
        FROM pg_attribute a
        JOIN pg_class c
            ON c.oid = a.attrelid
        JOIN pg_namespace n
            ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relname = %s
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum;
    """

    with connection.cursor() as cur:
        cur.execute(
            query,
            (schema, table)
        )

        return [row[0] for row in cur.fetchall()]


# ============================================================
# FOREIGN KEY
# ============================================================

def get_foreign_keys(connection, schema, tables):
    """
    Получает определения FOREIGN KEY для переносимых таблиц.

    test полностью исключён.
    """

    if not tables:
        return []

    query = """
        SELECT
            con.oid,
            child.relname AS child_table,
            con.conname AS constraint_name,
            pg_get_constraintdef(con.oid) AS constraint_definition
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
          AND child.relname = ANY(%s)
          AND parent.relname = ANY(%s)
          AND child.relname <> ALL(%s)
          AND parent.relname <> ALL(%s)

        ORDER BY child.relname, con.conname;
    """

    with connection.cursor() as cur:
        cur.execute(
            query,
            (
                schema,
                schema,
                tables,
                tables,
                list(EXCLUDED_TABLES),
                list(EXCLUDED_TABLES)
            )
        )

        return cur.fetchall()


def drop_foreign_keys(connection, foreign_keys):
    """
    Временно удаляет FOREIGN KEY.
    Сами таблицы и остальные ограничения не трогаются.
    """

    logger.info("")
    logger.info("=" * 70)
    logger.info("ВРЕМЕННОЕ УДАЛЕНИЕ FOREIGN KEY")
    logger.info("=" * 70)

    with connection.cursor() as cur:

        for _, table, constraint_name, definition in foreign_keys:

            logger.info(
                "Удаляем FK %s.%s",
                table,
                constraint_name
            )

            query = sql.SQL(
                "ALTER TABLE {}.{} DROP CONSTRAINT {}"
            ).format(
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(table),
                sql.Identifier(constraint_name)
            )

            cur.execute(query)

    connection.commit()

    logger.info(
        "✓ FOREIGN KEY временно удалены: %s",
        len(foreign_keys)
    )


def restore_foreign_keys(connection, foreign_keys):
    """
    Восстанавливает ранее удалённые FOREIGN KEY.
    """

    logger.info("")
    logger.info("=" * 70)
    logger.info("ВОССТАНОВЛЕНИЕ FOREIGN KEY")
    logger.info("=" * 70)

    with connection.cursor() as cur:

        for _, table, constraint_name, definition in foreign_keys:

            logger.info(
                "Восстанавливаем FK %s.%s",
                table,
                constraint_name
            )

            query = sql.SQL(
                "ALTER TABLE {}.{} ADD CONSTRAINT {} {}"
            ).format(
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(table),
                sql.Identifier(constraint_name),
                sql.SQL(definition)
            )

            cur.execute(query)

    connection.commit()

    logger.info(
        "✓ Все FOREIGN KEY восстановлены"
    )


# ============================================================
# ОЧИСТКА TARGET
# ============================================================

def clear_target_tables(connection, tables):
    """
    Удаляет данные из целевых таблиц.

    Используется DELETE, а не TRUNCATE.

    На момент вызова FOREIGN KEY уже удалены,
    поэтому циклические зависимости не мешают.

    test не трогается.
    """

    logger.info("")
    logger.info("=" * 70)
    logger.info("ОЧИСТКА TARGET")
    logger.info("=" * 70)

    with connection.cursor() as cur:

        for table in tables:

            if table in EXCLUDED_TABLES:
                continue

            query = sql.SQL(
                "DELETE FROM {}.{}"
            ).format(
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(table)
            )

            logger.info(
                "Очищаем %s.%s",
                TARGET_SCHEMA,
                table
            )

            cur.execute(query)

    connection.commit()

    logger.info(
        "✓ Данные target очищены"
    )


# ============================================================
# КОПИРОВАНИЕ ДАННЫХ
# ============================================================

def copy_table_data(source_conn, target_conn, table):
    """
    Копирует данные одной таблицы через COPY.

    Используются только колонки, которые есть
    и в source, и в target.
    """

    source_columns = get_columns(
        source_conn,
        SOURCE_SCHEMA,
        table
    )

    target_columns = get_columns(
        target_conn,
        TARGET_SCHEMA,
        table
    )

    columns = [
        column
        for column in source_columns
        if column in target_columns
    ]

    if not columns:

        logger.warning(
            "%s: нет общих колонок, пропускаем",
            table
        )

        return

    logger.info(
        "Копирование %s (%s колонок)...",
        table,
        len(columns)
    )

    # --------------------------------------------------------
    # SOURCE COPY
    # --------------------------------------------------------

    source_query = sql.SQL(
        """
        COPY (
            SELECT {}
            FROM {}.{}
        )
        TO STDOUT
        WITH (
            FORMAT CSV,
            HEADER FALSE,
            NULL '\\N'
        )
        """
    ).format(
        sql.SQL(", ").join(
            sql.Identifier(column)
            for column in columns
        ),
        sql.Identifier(SOURCE_SCHEMA),
        sql.Identifier(table)
    )

    # --------------------------------------------------------
    # TARGET COPY
    # --------------------------------------------------------

    target_query = sql.SQL(
        """
        COPY {}.{} ({})
        FROM STDIN
        WITH (
            FORMAT CSV,
            HEADER FALSE,
            NULL '\\N'
        )
        """
    ).format(
        sql.Identifier(TARGET_SCHEMA),
        sql.Identifier(table),
        sql.SQL(", ").join(
            sql.Identifier(column)
            for column in columns
        )
    )

    buffer = io.BytesIO()

    # SOURCE → память
    with source_conn.cursor() as source_cur:

        source_cur.copy_expert(
            source_query.as_string(source_conn),
            buffer
        )

    buffer.seek(0)

    # память → TARGET
    with target_conn.cursor() as target_cur:

        target_cur.copy_expert(
            target_query.as_string(target_conn),
            buffer
        )

    target_conn.commit()

    logger.info(
        "✓ %s перенесена",
        table
    )


# ============================================================
# КОЛИЧЕСТВО СТРОК
# ============================================================

def get_row_count(connection, schema, table):

    query = sql.SQL(
        "SELECT COUNT(*) FROM {}.{}"
    ).format(
        sql.Identifier(schema),
        sql.Identifier(table)
    )

    with connection.cursor() as cur:

        cur.execute(query)

        return cur.fetchone()[0]


# ============================================================
# SEQUENCES
# ============================================================

def get_sequences(connection, schema):

    query = """
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = %s
        ORDER BY sequence_name;
    """

    with connection.cursor() as cur:

        cur.execute(
            query,
            (schema,)
        )

        return [
            row[0]
            for row in cur.fetchall()
        ]


def get_sequence_owner(connection, schema, sequence):

    """
    Находит таблицу и колонку,
    которым принадлежит sequence.
    """

    query = """
        SELECT
            table_name,
            column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND column_default LIKE %s;
    """

    pattern = f"%{schema}.{sequence}%"

    with connection.cursor() as cur:

        cur.execute(
            query,
            (schema, pattern)
        )

        return cur.fetchone()


def sync_sequence(connection, schema, sequence):

    owner = get_sequence_owner(
        connection,
        schema,
        sequence
    )

    if not owner:
        return

    table_name, column_name = owner

    # test не трогаем
    if table_name in EXCLUDED_TABLES:
        return

    query = sql.SQL(
        """
        SELECT setval(
            {}.{},
            COALESCE(
                (SELECT MAX({})
                 FROM {}.{}),
                1
            ),
            EXISTS (
                SELECT 1
                FROM {}.{}
            )
        )
        """
    ).format(
        sql.Identifier(schema),
        sql.Identifier(sequence),

        sql.Identifier(column_name),

        sql.Identifier(schema),
        sql.Identifier(table_name),

        sql.Identifier(schema),
        sql.Identifier(table_name)
    )

    with connection.cursor() as cur:

        cur.execute(query)

    connection.commit()

    logger.info(
        "✓ Sequence %s синхронизирована",
        sequence
    )


def sync_all_sequences(connection):

    logger.info("")
    logger.info("=" * 70)
    logger.info("СИНХРОНИЗАЦИЯ SEQUENCES")
    logger.info("=" * 70)

    sequences = get_sequences(
        connection,
        TARGET_SCHEMA
    )

    for sequence in sequences:

        sync_sequence(
            connection,
            TARGET_SCHEMA,
            sequence
        )


# ============================================================
# ПРОВЕРКА ДАННЫХ
# ============================================================

def verify_data(
    source_conn,
    target_conn,
    tables
):

    logger.info("")
    logger.info("=" * 70)
    logger.info("ПРОВЕРКА КОЛИЧЕСТВА СТРОК")
    logger.info("=" * 70)

    errors = []

    for table in tables:

        source_count = get_row_count(
            source_conn,
            SOURCE_SCHEMA,
            table
        )

        target_count = get_row_count(
            target_conn,
            TARGET_SCHEMA,
            table
        )

        if source_count == target_count:

            logger.info(
                "✓ %-40s source=%s target=%s",
                table,
                source_count,
                target_count
            )

        else:

            logger.error(
                "✗ %-40s source=%s target=%s",
                table,
                source_count,
                target_count
            )

            errors.append(
                (
                    table,
                    source_count,
                    target_count
                )
            )

    return errors


# ============================================================
# ПРОВЕРКА FOREIGN KEY ПОСЛЕ ВОССТАНОВЛЕНИЯ
# ============================================================

def verify_foreign_keys(connection, foreign_keys):

    logger.info("")
    logger.info("=" * 70)
    logger.info("ПРОВЕРКА FOREIGN KEY")
    logger.info("=" * 70)

    # Если ADD CONSTRAINT прошёл успешно,
    # PostgreSQL уже проверил существующие данные.
    logger.info(
        "✓ PostgreSQL успешно восстановил %s FOREIGN KEY",
        len(foreign_keys)
    )


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def migrate():

    logger.info("=" * 70)
    logger.info("ПЕРЕНОС ДАННЫХ")
    logger.info("=" * 70)

    source_conn = None
    target_conn = None

    foreign_keys = []
    foreign_keys_dropped = False
    foreign_keys_restored = False

    try:

        # ----------------------------------------------------
        # Подключение
        # ----------------------------------------------------

        logger.info(
            "Подключение к source: %s",
            SOURCE_DB
        )

        source_conn = get_connection(
            SOURCE_DB
        )

        logger.info(
            "Подключение к target: %s",
            TARGET_DB
        )

        target_conn = get_connection(
            TARGET_DB
        )

        # ----------------------------------------------------
        # Таблицы
        # ----------------------------------------------------

        source_tables = get_tables(
            source_conn,
            SOURCE_SCHEMA
        )

        target_tables = get_tables(
            target_conn,
            TARGET_SCHEMA
        )

        logger.info(
            "Таблиц в source для переноса: %s",
            len(source_tables)
        )

        logger.info(
            "Таблиц в target: %s",
            len(target_tables)
        )

        logger.info(
            "Таблица test полностью исключена."
        )

        # ----------------------------------------------------
        # Проверяем, что все таблицы существуют
        # ----------------------------------------------------

        missing_tables = [
            table
            for table in source_tables
            if table not in target_tables
        ]

        if missing_tables:

            logger.error(
                "В target отсутствуют таблицы:"
            )

            for table in missing_tables:

                logger.error(
                    "  %s",
                    table
                )

            raise RuntimeError(
                "Не все таблицы source существуют в target."
            )

        # ----------------------------------------------------
        # Получаем FOREIGN KEY
        # ----------------------------------------------------

        foreign_keys = get_foreign_keys(
            target_conn,
            TARGET_SCHEMA,
            source_tables
        )

        logger.info(
            "Найдено FOREIGN KEY для переноса: %s",
            len(foreign_keys)
        )

        # ----------------------------------------------------
        # Удаляем FK
        # ----------------------------------------------------

        drop_foreign_keys(
            target_conn,
            foreign_keys
        )

        foreign_keys_dropped = True

        # ----------------------------------------------------
        # Очищаем target
        # ----------------------------------------------------

        clear_target_tables(
            target_conn,
            source_tables
        )

        # ----------------------------------------------------
        # Копируем данные
        # ----------------------------------------------------

        logger.info("")
        logger.info("=" * 70)
        logger.info("НАЧИНАЕМ ПЕРЕНОС ДАННЫХ")
        logger.info("=" * 70)

        for number, table in enumerate(
            source_tables,
            start=1
        ):

            logger.info("")

            logger.info(
                "[%s/%s] %s",
                number,
                len(source_tables),
                table
            )

            copy_table_data(
                source_conn,
                target_conn,
                table
            )

        # ----------------------------------------------------
        # Синхронизация sequences
        # ----------------------------------------------------

        sync_all_sequences(
            target_conn
        )

        # ----------------------------------------------------
        # ВОССТАНАВЛИВАЕМ FOREIGN KEY
        # ----------------------------------------------------

        restore_foreign_keys(
            target_conn,
            foreign_keys
        )

        foreign_keys_restored = True

        # ----------------------------------------------------
        # Проверка количества строк
        # ----------------------------------------------------

        errors = verify_data(
            source_conn,
            target_conn,
            source_tables
        )

        # ----------------------------------------------------
        # Проверка FK
        # ----------------------------------------------------

        verify_foreign_keys(
            target_conn,
            foreign_keys
        )

        # ----------------------------------------------------
        # Итог
        # ----------------------------------------------------

        logger.info("")
        logger.info("=" * 70)

        if errors:

            logger.error(
                "ПЕРЕНОС ЗАВЕРШЁН С ОШИБКАМИ"
            )

            for (
                table,
                source_count,
                target_count
            ) in errors:

                logger.error(
                    "%s: source=%s target=%s",
                    table,
                    source_count,
                    target_count
                )

        else:

            logger.info(
                "✓ ПЕРЕНОС ДАННЫХ УСПЕШНО ЗАВЕРШЁН"
            )

        logger.info("=" * 70)

    except Exception:

        logger.exception(
            "Ошибка во время переноса"
        )

        # ----------------------------------------------------
        # Если FK были удалены, но восстановить их не успели,
        # пытаемся восстановить их обязательно.
        # ----------------------------------------------------

        if (
            target_conn
            and foreign_keys_dropped
            and not foreign_keys_restored
        ):

            logger.error(
                "Пытаемся восстановить FOREIGN KEY после ошибки..."
            )

            try:

                restore_foreign_keys(
                    target_conn,
                    foreign_keys
                )

                logger.info(
                    "✓ FOREIGN KEY восстановлены после ошибки"
                )

            except Exception:

                logger.exception(
                    "КРИТИЧЕСКАЯ ОШИБКА: "
                    "не удалось восстановить FOREIGN KEY"
                )

        raise

    finally:

        if source_conn:
            source_conn.close()

        if target_conn:
            target_conn.close()

        logger.info(
            "Соединения закрыты."
        )


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    migrate()
