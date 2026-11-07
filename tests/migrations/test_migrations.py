"""Migration checks for an empty, disposable PostgreSQL database.

Run: python -m unittest discover -s tests/migrations -v
"""

import os
from pathlib import Path
import subprocess
import sys
import unittest

from sqlalchemy import create_engine, inspect, text

from app.core.config import settings


ROOT = Path(__file__).resolve().parents[2]
TABLES = {
    "available_shifts", "members", "plans", "users", "memberships",
    "reservations", "attendances", "payments",
}


def alembic(*args, env=None):
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout


class OfflineMigrationsTest(unittest.TestCase):
    def test_generates_schema_without_a_database_connection(self):
        env = dict(os.environ, DATABASE_URL="", DB_HOST="unreachable.invalid")
        sql = alembic("upgrade", "head", "--sql", env=env)
        for table in TABLES:
            self.assertIn(f"CREATE TABLE {table}", sql)

    def test_explicit_url_overrides_fields_and_accepts_percent_encoding(self):
        env = dict(
            os.environ,
            DATABASE_URL="postgresql://ci:p%40ss@unreachable.invalid/ci",
            DB_PORT="1",
        )
        sql = alembic("upgrade", "head", "--sql", env=env)
        self.assertIn("CREATE TABLE members", sql)


class PostgreSQLMigrationsTest(unittest.TestCase):
    def test_upgrade_creates_schema_and_can_run_twice(self):
        engine = create_engine(settings.get_database_url())
        self.addCleanup(engine.dispose)
        self.assertFalse(
            set(inspect(engine).get_table_names()) & TABLES,
            "Use an empty, disposable database for this test.",
        )

        alembic("upgrade", "head")
        alembic("upgrade", "head")

        inspector = inspect(engine)
        self.assertEqual(set(inspector.get_table_names()), TABLES | {"alembic_version"})
        self.assertEqual(
            {fk["referred_table"] for fk in inspector.get_foreign_keys("attendances")},
            {"members", "reservations"},
        )
        with engine.connect() as connection:
            self.assertEqual(
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one(),
                "37212ae7fe48",
            )


if __name__ == "__main__":
    unittest.main()
