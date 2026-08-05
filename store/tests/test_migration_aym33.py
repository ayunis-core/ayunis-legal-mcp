"""Database-level regression test for the AYM-33 migration."""

import os
import subprocess
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_MIGRATION_TESTS") != "1",
    reason="Set RUN_MIGRATION_TESTS=1 with PostgreSQL available",
)
def test_migration_backfills_all_rows_and_changes_document_uniqueness():
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    password = os.getenv("POSTGRES_PASSWORD", "postgres_password")
    database_name = f"legal_mcp_migration_{uuid.uuid4().hex}"
    admin_url = f"postgresql://postgres:{password}@{host}:{port}/postgres"
    test_url = f"postgresql://postgres:{password}@{host}:{port}/{database_name}"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    test_engine = None

    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))

        environment = os.environ.copy()
        environment["POSTGRES_DB"] = database_name
        subprocess.run(
            ["alembic", "upgrade", "a1b2c3d4e5f6"],
            cwd="/app",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        test_engine = create_engine(test_url)
        vector = "[" + ",".join(["0"] * 2560) + "]"
        with test_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO legal_texts
                        (text, text_vector, code, section, sub_section)
                    VALUES (:content, CAST(:vector AS vector), 'shared', '§ 1', '1')
                    """
                ),
                {"content": "Federal text", "vector": vector},
            )

        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        with test_engine.begin() as connection:
            federal = connection.execute(
                text(
                    """
                    SELECT source, jurisdiction, document_id, document_title
                    FROM legal_texts
                    WHERE text = 'Federal text'
                    """
                )
            ).one()
            assert federal == (
                "gesetze-im-internet",
                "DE",
                "shared",
                "shared",
            )
            connection.execute(
                text(
                    """
                    INSERT INTO legal_texts (
                        text, text_vector, code, source, jurisdiction,
                        document_id, document_title, content_hash, section, sub_section
                    ) VALUES (
                        'State text', CAST(:vector AS vector), 'shared', 'state-source',
                        'DE-BY', 'opaque-state-id', 'State law', :content_hash, '§ 1', '1'
                    )
                    """
                ),
                {"vector": vector, "content_hash": "a" * 64},
            )
            assert connection.execute(
                text(
                    "SELECT count(*) FROM legal_texts WHERE code = 'shared' AND section = '§ 1'"
                )
            ).scalar_one() == 2
            # The legacy schema cannot represent the collision; remove only the
            # post-upgrade fixture before verifying a lossless downgrade.
            connection.execute(text("DELETE FROM legal_texts WHERE text = 'State text'"))

        subprocess.run(
            ["alembic", "downgrade", "a1b2c3d4e5f6"],
            cwd="/app",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "source" not in {
            column["name"] for column in inspect(test_engine).get_columns("legal_texts")
        }
        with test_engine.connect() as connection:
            assert connection.execute(
                text("SELECT text FROM legal_texts WHERE code = 'shared'")
            ).scalar_one() == "Federal text"
    finally:
        if test_engine is not None:
            test_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()
