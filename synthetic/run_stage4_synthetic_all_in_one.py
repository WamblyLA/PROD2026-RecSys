from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"
SRC_ROOT = ML_ROOT / "src"
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ml.infra.db.session import engine
from synthetic.db_helpers import ensure_required_tables_exist
from synthetic.run_stage4_synthetic_verification import (
    DEFAULT_CANDIDATES_PER_GROUP,
    DEFAULT_GROUPS_PER_ACTOR,
    DEFAULT_SAMPLE_SIZE,
    DEFAULT_SEED,
    DEFAULT_SMOKE_ROWS,
    run_stage4_synthetic_verification,
)

BACKEND_COMPOSE_FILE = PROJECT_ROOT / "backend" / "docker-compose.yaml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run stage_4 synthetic verification in one command: "
            "auto-start Postgres/API bootstrap if needed, run verification, print artifacts."
        )
    )
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--groups-per-actor", type=int, default=DEFAULT_GROUPS_PER_ACTOR)
    parser.add_argument("--candidates-per-group", type=int, default=DEFAULT_CANDIDATES_PER_GROUP)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--smoke-rows", type=int, default=DEFAULT_SMOKE_ROWS)
    parser.add_argument("--db-timeout-seconds", type=int, default=180)
    parser.add_argument("--keep-postgres", action="store_true")
    return parser.parse_args()


def _run_compose_command(args: list[str]) -> str:
    if not BACKEND_COMPOSE_FILE.exists():
        raise RuntimeError(f"Backend compose file is missing: {BACKEND_COMPOSE_FILE}")
    command = [
        "docker",
        "compose",
        "-f",
        str(BACKEND_COMPOSE_FILE),
        *args,
    ]
    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Docker compose command failed: "
            f"{' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def _running_services() -> set[str]:
    output = _run_compose_command(["ps", "--status", "running", "--services"])
    return {
        line.strip()
        for line in output.splitlines()
        if line.strip()
    }


def _is_db_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _wait_for_db_ready(timeout_seconds: int) -> None:
    deadline = time.monotonic() + max(timeout_seconds, 1)
    while time.monotonic() < deadline:
        if _is_db_ready():
            return
        time.sleep(1.0)
    raise RuntimeError(
        f"Postgres is not reachable after {timeout_seconds} seconds."
    )


def _wait_for_required_tables(timeout_seconds: int) -> None:
    deadline = time.monotonic() + max(timeout_seconds, 1)
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            ensure_required_tables_exist()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(1.0)
    raise RuntimeError(
        "Required backend tables are still missing after bootstrap timeout. "
        f"Last error: {last_error}"
    )


def main() -> None:
    args = _parse_args()
    running_before = _running_services()
    postgres_running_before = "postgres" in running_before
    api_running_before = "api" in running_before

    started_postgres_here = False
    started_api_here = False

    try:
        if not _is_db_ready():
            print("DB is unavailable. Starting backend postgres service...")
            _run_compose_command(["up", "-d", "postgres"])
            started_postgres_here = not postgres_running_before
            _wait_for_db_ready(args.db_timeout_seconds)

        try:
            ensure_required_tables_exist()
        except Exception:
            print("Required tables are missing. Starting backend API for schema bootstrap...")
            _run_compose_command(["up", "-d", "api"])
            started_api_here = not api_running_before
            _wait_for_required_tables(args.db_timeout_seconds)

        summary = run_stage4_synthetic_verification(
            sample_size=args.sample_size,
            groups_per_actor=args.groups_per_actor,
            candidates_per_group=args.candidates_per_group,
            seed=args.seed,
            smoke_rows=args.smoke_rows,
        )
        summary_path = Path(summary.report_dir) / "final_summary.json"
        summary_payload = asdict(summary)
        summary_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        summary_payload["final_summary_path"] = str(summary_path)
        summary_path.write_text(
            json.dumps(summary_payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        print(f"final summary: {summary_path}")
        print(f"overview plot: {summary.verification_overview_path}")
        print(f"train_dataset: {summary.train_dataset_path}")
    finally:
        if started_api_here:
            try:
                print("Stopping bootstrap API service...")
                _run_compose_command(["stop", "api"])
            except Exception as exc:
                print(f"warning: unable to stop api service cleanly: {exc}")

        if started_postgres_here and not args.keep_postgres:
            try:
                print("Stopping postgres service started by this run...")
                _run_compose_command(["stop", "postgres"])
            except Exception as exc:
                print(f"warning: unable to stop postgres service cleanly: {exc}")


if __name__ == "__main__":
    main()
