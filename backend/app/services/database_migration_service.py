"""Database migration service for switching between SQLite, PostgreSQL, and MySQL."""
import logging
from typing import Dict, Any, List

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.db.session import Base

logger = logging.getLogger(__name__)

# Tables in FK-safe insertion order
TABLE_ORDER: List[str] = [
    "setup_status",
    "mailbox_configs",
    "output_configs",
    "parse_jobs",
    "monitoring_jobs",   # FK → mailbox_configs
    "parsed_reports",    # FK → parse_jobs
    "activity_logs",
]

BATCH_SIZE = 1000


class DatabaseMigrationService:
    """Handles testing connections and migrating data between databases."""

    def test_connection(self, database_url: str) -> Dict[str, Any]:
        """Test connectivity to a database.

        Returns:
            dict with success, message, and optional details.
        """
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return {
                "success": True,
                "message": "Connection successful.",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {e}",
                "details": {"error_type": type(e).__name__},
            }

    def get_table_counts(self, database_url: str) -> Dict[str, int]:
        """Get row counts for all known tables in the given database."""
        engine = create_engine(database_url)
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        counts: Dict[str, int] = {}

        with engine.connect() as conn:
            for table_name in TABLE_ORDER:
                if table_name in existing_tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    counts[table_name] = result.scalar() or 0
                else:
                    counts[table_name] = 0

        engine.dispose()
        return counts

    def migrate(self, source_url: str, target_url: str) -> Dict[str, Any]:
        """Migrate all data from source database to target database.

        Creates tables in the target, copies data table by table in FK-safe
        order, and resets PostgreSQL sequences.

        The source database is never modified.

        Returns:
            dict with success, message, tables_migrated, row_counts.
        """
        source_engine = create_engine(source_url)
        target_engine = create_engine(target_url, pool_pre_ping=True)

        try:
            # 1. Create all tables in target
            logger.info("Creating tables in target database...")
            Base.metadata.create_all(target_engine)

            SourceSession = sessionmaker(bind=source_engine)
            TargetSession = sessionmaker(bind=target_engine)

            row_counts: Dict[str, int] = {}
            tables_migrated = 0

            # 2. Copy data table by table
            for table_name in TABLE_ORDER:
                table = Base.metadata.tables.get(table_name)
                if table is None:
                    logger.warning(f"Table '{table_name}' not in metadata, skipping.")
                    continue

                logger.info(f"Migrating table: {table_name}")

                with SourceSession() as source_sess:
                    rows = source_sess.execute(table.select()).fetchall()

                if not rows:
                    row_counts[table_name] = 0
                    tables_migrated += 1
                    logger.info(f"  {table_name}: 0 rows (empty)")
                    continue

                # Get column names from the table
                columns = [c.name for c in table.columns]

                with TargetSession() as target_sess:
                    # Clear any existing data in target table
                    target_sess.execute(table.delete())
                    target_sess.commit()

                    # Batch insert
                    row_dicts = [dict(zip(columns, row)) for row in rows]
                    for i in range(0, len(row_dicts), BATCH_SIZE):
                        batch = row_dicts[i:i + BATCH_SIZE]
                        target_sess.execute(table.insert(), batch)
                    target_sess.commit()

                row_counts[table_name] = len(rows)
                tables_migrated += 1
                logger.info(f"  {table_name}: {len(rows)} rows migrated")

            # 3. Reset PostgreSQL sequences
            if target_url.startswith("postgresql"):
                self._reset_pg_sequences(target_engine)

            logger.info(
                f"Migration complete: {tables_migrated} tables, "
                f"{sum(row_counts.values())} total rows"
            )

            return {
                "success": True,
                "message": "Migration completed successfully.",
                "tables_migrated": tables_migrated,
                "row_counts": row_counts,
            }

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            # Attempt cleanup: drop tables in target
            try:
                Base.metadata.drop_all(target_engine)
                logger.info("Cleaned up target database after failure.")
            except Exception as cleanup_err:
                logger.error(f"Cleanup also failed: {cleanup_err}")

            return {
                "success": False,
                "message": f"Migration failed: {e}",
                "tables_migrated": 0,
                "row_counts": {},
            }
        finally:
            source_engine.dispose()
            target_engine.dispose()

    def purge_all_data(self, database_url: str) -> Dict[str, Any]:
        """Delete all rows from every known table (reverse FK order).

        Returns:
            dict with success, message, rows_deleted (per table).
        """
        engine = create_engine(database_url)
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        try:
            rows_deleted: Dict[str, int] = {}

            with engine.connect() as conn:
                # Delete in reverse FK order to respect constraints
                for table_name in reversed(TABLE_ORDER):
                    if table_name not in existing_tables:
                        continue
                    result = conn.execute(text(f"DELETE FROM {table_name}"))
                    rows_deleted[table_name] = result.rowcount
                    logger.info(f"  Purged {table_name}: {result.rowcount} rows deleted")
                conn.commit()

            total = sum(rows_deleted.values())
            logger.info(f"Database purge complete: {total} total rows deleted")

            return {
                "success": True,
                "message": f"Database purged successfully. {total} rows deleted.",
                "rows_deleted": rows_deleted,
            }
        except Exception as e:
            logger.error(f"Database purge failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Purge failed: {e}",
                "rows_deleted": {},
            }
        finally:
            engine.dispose()

    def _reset_pg_sequences(self, engine):
        """Reset PostgreSQL auto-increment sequences to MAX(id) + 1."""
        with engine.connect() as conn:
            for table_name in TABLE_ORDER:
                table = Base.metadata.tables.get(table_name)
                if table is None:
                    continue
                # Only reset if table has an 'id' column
                if "id" not in [c.name for c in table.columns]:
                    continue

                seq_name = f"{table_name}_id_seq"
                try:
                    result = conn.execute(
                        text(f"SELECT MAX(id) FROM {table_name}")
                    )
                    max_id = result.scalar() or 0
                    conn.execute(
                        text(f"SELECT setval('{seq_name}', :val, true)"),
                        {"val": max(max_id, 1)},
                    )
                    conn.commit()
                    logger.info(f"  Reset sequence {seq_name} to {max_id}")
                except Exception as e:
                    logger.warning(f"  Could not reset sequence {seq_name}: {e}")


# Module-level singleton
migration_service = DatabaseMigrationService()
