"""Regression tests for the store API container startup contract."""

import os
import subprocess
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPOSITORY_ROOT / "store" / "entrypoint.sh"


def write_executable(path: Path, content: str) -> None:
    """Write an executable test command."""
    path.write_text(content)
    path.chmod(0o755)


def run_entrypoint(tmp_path: Path, migration_exit_code: int = 0):
    """Run the container entrypoint with observable fake commands."""
    events = tmp_path / "events"
    binary_directory = tmp_path / "bin"
    binary_directory.mkdir()
    write_executable(
        binary_directory / "alembic",
        "#!/bin/sh\n"
        f'echo "alembic $*" >> "{events}"\n'
        f"exit {migration_exit_code}\n",
    )
    write_executable(
        binary_directory / "serve-store",
        "#!/bin/sh\n" f'echo "server $*" >> "{events}"\n',
    )
    environment = os.environ.copy()
    environment["PATH"] = f"{binary_directory}:{environment['PATH']}"

    result = subprocess.run(
        [str(ENTRYPOINT), "serve-store", "--port", "8000"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    recorded_events = events.read_text().splitlines() if events.exists() else []
    return result, recorded_events


@pytest.mark.unit
def test_container_migrates_database_before_starting_store_api(tmp_path):
    result, events = run_entrypoint(tmp_path)

    assert result.returncode == 0
    assert events == ["alembic upgrade head", "server --port 8000"]


@pytest.mark.unit
def test_container_does_not_start_store_api_when_migration_fails(tmp_path):
    result, events = run_entrypoint(tmp_path, migration_exit_code=17)

    assert result.returncode == 17
    assert events == ["alembic upgrade head"]
