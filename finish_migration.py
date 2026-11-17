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

# Оставь здесь свой пароль локально.
# Я намеренно не вставляю его в код.
PASSWORD = "eGmFdAEO_1@@1_"

SCHEMA = "geo_umzr"

# ЭТУ таблицу НЕ ТРОГАЕМ
EXCLUDED_TABLES = {"test"}


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
# ПОЛУЧЕНИЕ ТАБЛИЦ
# ============================================================

def get_tables(conn):
    """
    Возвращает таблицы схемы SCHEMA,
    кроме EXCLUDED_TABLES.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (SCHEMA,)
        )

        tables = {
            row[0]
            for row in cur.fetchall()
            if row[0] not in EXCLUDED_TABLES
        }

    return sorted(tables)


# ============================================================
# ПРОВЕРКА КОЛИЧЕСТВА СТРОК
# ============================================================

def get_row_count(conn, table_name):
    with conn.cursor() as cur:
        query = sql.SQL(
            "SELECT COUNT(*) FROM {}.{}"
        ).format(
            sql.Identifier(SCHEMA),
            sql.Identifier(table_name)
        )

        cur.execute(query)
        return cur.fetchone()[0]


def verify_row_counts(source_conn, target_conn, tables):
    """
    Проверяем, что данные действительно полностью скопировались.
    Ничего не изменяет.
    """

    print()
    print("=" * 70)
    print("ПРОВЕРКА КОЛИЧЕСТВА СТРОК")
    print("=" * 70)

    errors = []

    for table in tables:

        source_count = get_row_count(source_conn, table)
        target_count = get_row_count(target_conn, table)

        if source_count == target_count:
            print(
                f"[OK] {table}: "
                f"{source_count} строк"
            )
        else:
            print(
                f"[ERROR] {table}: "
                f"source={source_count}, "
                f"target={target_count}"
            )

            errors.append(
                (
                    table,
                    source_count,
                    target_count
                )
            )

    print()

    if errors:
        print("Найдены расхождения в количестве строк.")

        for table, source_count, target_count in errors:
            print(
                f"  {table}: "
                f"source={source_count}, "
                f"target={target_count}"
            )

        raise RuntimeError(
            "Количество строк не совпадает. "
            "Завершение миграции остановлено."
        )

    print("Количество строк во всех таблицах совпадает.")


# ============================================================
# ПОИСК SEQUENCE
# ============================================================

def get_sequences(conn):
    """
    Находит sequence, которые принадлежат колонкам таблиц.

    Например:

        geo_umzr.tasks.id
            ->
        geo_umzr.tasks_id_seq

    test автоматически исключается.
    """

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT
                seq_ns.nspname AS sequence_schema,
                seq.relname AS sequence_name,

                tbl_ns.nspname AS table_schema,
                tbl.relname AS table_name,

                att.attname AS column_name

            FROM pg_class seq

            JOIN pg_namespace seq_ns
                ON seq_ns.oid = seq.relnamespace

            JOIN pg_depend dep
                ON dep.objid = seq.oid
               AND dep.deptype IN ('a', 'i')

            JOIN pg_class tbl
                ON tbl.oid = dep.refobjid

            JOIN pg_namespace tbl_ns
                ON tbl_ns.oid = tbl.relnamespace

            JOIN pg_attribute att
                ON att.attrelid = tbl.oid
               AND att.attnum = dep.refobjsubid

            WHERE seq.relkind = 'S'
              AND seq_ns.nspname = %s
              AND tbl_ns.nspname = %s
              AND tbl.relkind IN ('r', 'p')
              AND tbl.relname <> ALL(%s)

            ORDER BY tbl.relname, att.attname
            """,
            (
                SCHEMA,
                SCHEMA,
                list(EXCLUDED_TABLES)
            )
        )

        return cur.fetchall()


# ============================================================
# СИНХРОНИЗАЦИЯ SEQUENCE
# ============================================================

def sync_sequences(target_conn):
    """
    Синхронизирует sequence с максимальным значением
    соответствующего ID в таблице.

    ВАЖНО:
    test здесь не затрагивается.
    """

    print()
    print("=" * 70)
    print("СИНХРОНИЗАЦИЯ SEQUENCE")
    print("=" * 70)

    sequences = get_sequences(target_conn)

    print(f"Найдено sequence: {len(sequences)}")

    errors = []

    for (
        sequence_schema,
        sequence_name,
        table_schema,
        table_name,
        column_name
    ) in sequences:

        try:

            # ------------------------------------------------
            # Получаем MAX(id)
            # ------------------------------------------------

            with target_conn.cursor() as cur:

                max_query = sql.SQL(
                    """
                    SELECT MAX({})
                    FROM {}.{}
                    """
                ).format(
                    sql.Identifier(column_name),
                    sql.Identifier(table_schema),
                    sql.Identifier(table_name)
                )

                cur.execute(max_query)

                max_value = cur.fetchone()[0]

            # ------------------------------------------------
            # Синхронизируем sequence
            # ------------------------------------------------

            sequence_full_name = (
                f"{sequence_schema}.{sequence_name}"
            )

            with target_conn.cursor() as cur:

                if max_value is None:

                    # Таблица пустая.
                    #
                    # false означает:
                    # следующее значение будет 1.

                    cur.execute(
                        """
                        SELECT setval(
                            %s,
                            1,
                            false
                        )
                        """,
                        (sequence_full_name,)
                    )

                    print(
                        f"[OK] {sequence_name}: "
                        f"таблица {table_name} пустая -> 1"
                    )

                else:

                    # Следующий nextval() даст max_value + 1

                    cur.execute(
                        """
                        SELECT setval(
                            %s,
                            %s,
                            true
                        )
                        """,
                        (
                            sequence_full_name,
                            max_value
                        )
                    )

                    print(
                        f"[OK] {sequence_name}: "
                        f"{table_name}.{column_name} "
                        f"-> {max_value}"
                    )

            target_conn.commit()

        except Exception as e:

            target_conn.rollback()

            print(
                f"[ERROR] {sequence_name}: {e}"
            )

            errors.append(
                (
                    sequence_name,
                    table_name,
                    column_name,
                    str(e)
                )
            )

    print()

    if errors:

        print(
            "Некоторые sequence не удалось синхронизировать:"
        )

        for (
            sequence_name,
            table_name,
            column_name,
            error
        ) in errors:

            print(
                f"  {sequence_name} "
                f"({table_name}.{column_name}): "
                f"{error}"
            )

    else:

        print(
            "Все sequence успешно синхронизированы."
        )

    return errors


# ============================================================
# ПОЛУЧЕНИЕ FOREIGN KEY ИЗ SOURCE
# ============================================================

def get_foreign_keys(source_conn, tables):
    """
    Получаем определения FK из исходной БД.

    Берём их именно из source, потому что в target
    FK были временно удалены предыдущим скриптом.
    """

    with source_conn.cursor() as cur:

        cur.execute(
            """
            SELECT
                child.relname AS child_table,
                con.conname AS constraint_name,
                pg_get_constraintdef(con.oid) AS constraint_definition,
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

              AND child.relname = ANY(%s)
              AND parent.relname = ANY(%s)

              AND child.relname <> ALL(%s)
              AND parent.relname <> ALL(%s)

            ORDER BY
                child.relname,
                con.conname
            """,
            (
                SCHEMA,
                SCHEMA,
                tables,
                tables,
                list(EXCLUDED_TABLES),
                list(EXCLUDED_TABLES)
            )
        )

        return cur.fetchall()


# ============================================================
# ПРОВЕРКА, СУЩЕСТВУЕТ ЛИ FK
# ============================================================

def constraint_exists(
    target_conn,
    table_name,
    constraint_name
):
    with target_conn.cursor() as cur:

        cur.execute(
            """
            SELECT 1

            FROM pg_constraint con

            JOIN pg_class tbl
                ON tbl.oid = con.conrelid

            JOIN pg_namespace ns
                ON ns.oid = tbl.relnamespace

            WHERE ns.nspname = %s
              AND tbl.relname = %s
              AND con.conname = %s

            LIMIT 1
            """,
            (
                SCHEMA,
                table_name,
                constraint_name
            )
        )

        return cur.fetchone() is not None


# ============================================================
# ВОССТАНОВЛЕНИЕ FOREIGN KEY
# ============================================================

def restore_foreign_keys(
    source_conn,
    target_conn,
    tables
):
    """
    Восстанавливает FK в target по определениям
    из source.

    Каждый FK добавляется отдельной транзакцией,
    чтобы ошибка одного FK не сломала остальные.
    """

    print()
    print("=" * 70)
    print("ВОССТАНОВЛЕНИЕ FOREIGN KEY")
    print("=" * 70)

    foreign_keys = get_foreign_keys(
        source_conn,
        tables
    )

    print(
        f"Найдено FK в source: "
        f"{len(foreign_keys)}"
    )

    errors = []
    restored = 0
    skipped = 0

    for (
        child_table,
        constraint_name,
        constraint_definition,
        parent_table
    ) in foreign_keys:

        try:

            # ------------------------------------------------
            # Если FK уже существует — ничего не делаем.
            # ------------------------------------------------

            if constraint_exists(
                target_conn,
                child_table,
                constraint_name
            ):

                print(
                    f"[SKIP] {child_table}."
                    f"{constraint_name} "
                    f"(уже существует)"
                )

                skipped += 1
                continue

            # ------------------------------------------------
            # Добавляем FK
            # ------------------------------------------------

            query = sql.SQL(
                """
                ALTER TABLE {}.{}
                ADD CONSTRAINT {}
                {}
                """
            ).format(
                sql.Identifier(SCHEMA),
                sql.Identifier(child_table),
                sql.Identifier(constraint_name),
                sql.SQL(constraint_definition)
            )

            with target_conn.cursor() as cur:
                cur.execute(query)

            target_conn.commit()

            print(
                f"[OK] {child_table}."
                f"{constraint_name} "
                f"-> {parent_table}"
            )

            restored += 1

        except Exception as e:

            target_conn.rollback()

            print(
                f"[ERROR] {child_table}."
                f"{constraint_name}: {e}"
            )

            errors.append(
                (
                    child_table,
                    constraint_name,
                    parent_table,
                    str(e)
                )
            )

    print()
    print(
        f"Восстановлено FK: {restored}"
    )
    print(
        f"Пропущено FK: {skipped}"
    )
    print(
        f"Ошибок FK: {len(errors)}"
    )

    return foreign_keys, errors


# ============================================================
# ПРОВЕРКА КОЛИЧЕСТВА FK
# ============================================================

def count_foreign_keys(conn, tables):
    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT COUNT(*)

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
            """,
            (
                SCHEMA,
                SCHEMA,
                tables,
                tables,
                list(EXCLUDED_TABLES),
                list(EXCLUDED_TABLES)
            )
        )

        return cur.fetchone()[0]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ЗАВЕРШЕНИЕ МИГРАЦИИ geo_umzr")
    print("=" * 70)

    source_conn = None
    target_conn = None

    try:

        # ----------------------------------------------------
        # Подключение
        # ----------------------------------------------------

        print()
        print("Подключение к SOURCE...")

        source_conn = get_connection(SOURCE_DB)

        print(
            f"[OK] SOURCE: {SOURCE_DB}"
        )

        print()
        print("Подключение к TARGET...")

        target_conn = get_connection(TARGET_DB)

        print(
            f"[OK] TARGET: {TARGET_DB}"
        )

        # ----------------------------------------------------
        # Таблицы
        # ----------------------------------------------------

        source_tables = set(
            get_tables(source_conn)
        )

        target_tables = set(
            get_tables(target_conn)
        )

        tables = sorted(
            source_tables & target_tables
        )

        print()
        print(
            f"Таблиц для завершения: "
            f"{len(tables)}"
        )

        print(
            "Исключённые таблицы:",
            ", ".join(sorted(EXCLUDED_TABLES))
        )

        # ----------------------------------------------------
        # Проверка таблиц
        # ----------------------------------------------------

        if not tables:
            raise RuntimeError(
                "Не найдено ни одной таблицы для миграции."
            )

        # ----------------------------------------------------
        # 1. Проверяем данные
        # ----------------------------------------------------

        verify_row_counts(
            source_conn,
            target_conn,
            tables
        )

        # ----------------------------------------------------
        # 2. Синхронизируем sequence
        # ----------------------------------------------------

        sequence_errors = sync_sequences(
            target_conn
        )

        # ----------------------------------------------------
        # 3. Восстанавливаем FK
        # ----------------------------------------------------

        foreign_keys, fk_errors = restore_foreign_keys(
            source_conn,
            target_conn,
            tables
        )

        # ----------------------------------------------------
        # 4. Итоговая проверка FK
        # ----------------------------------------------------

        source_fk_count = len(
            foreign_keys
        )

        target_fk_count = count_foreign_keys(
            target_conn,
            tables
        )

        print()
        print("=" * 70)
        print("ИТОГОВАЯ ПРОВЕРКА")
        print("=" * 70)

        print(
            f"FK в SOURCE: {source_fk_count}"
        )

        print(
            f"FK в TARGET: {target_fk_count}"
        )

        # ----------------------------------------------------
        # Итог
        # ----------------------------------------------------

        print()

        if (
            target_fk_count == source_fk_count
            and not fk_errors
        ):

            print("=" * 70)
            print("МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА")
            print("=" * 70)

            if sequence_errors:
                print()
                print(
                    "ВНИМАНИЕ: данные и FK восстановлены, "
                    "но некоторые sequence не удалось "
                    "синхронизировать."
                )

        else:

            print("=" * 70)
            print("МИГРАЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ")
            print("=" * 70)

            print()
            print(
                "Некоторые FK не удалось восстановить."
            )

            if fk_errors:

                for (
                    child_table,
                    constraint_name,
                    parent_table,
                    error
                ) in fk_errors:

                    print()
                    print(
                        f"FK: {child_table}."
                        f"{constraint_name}"
                    )

                    print(
                        f"Parent: {parent_table}"
                    )

                    print(
                        f"Ошибка: {error}"
                    )

    except Exception as e:

        print()
        print("=" * 70)
        print("КРИТИЧЕСКАЯ ОШИБКА")
        print("=" * 70)

        print(e)

        if target_conn:
            target_conn.rollback()

    finally:

        if source_conn:
            source_conn.close()

        if target_conn:
            target_conn.close()

        print()
        print("Соединения закрыты.")


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    main()
