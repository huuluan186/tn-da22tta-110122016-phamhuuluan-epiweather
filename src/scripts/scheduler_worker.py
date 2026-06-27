"""
Docker scheduler worker for EpiWatch pipeline jobs.

Runs as a singleton container separate from FastAPI so scheduled data refresh
does not depend on the API process and does not duplicate across API replicas.
"""

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_script(name: str, args: list[str] | None = None) -> None:
    cmd = [sys.executable, str(SCRIPTS_DIR / name), *(args or []), "--trigger", "scheduled"]
    print(f"[scheduler] running: {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, timeout=3600)
    if proc.returncode == 0:
        print(f"[scheduler] {name} OK", flush=True)
        return
    print(f"[scheduler] {name} failed rc={proc.returncode}", flush=True)
    raise RuntimeError(f"{name} failed rc={proc.returncode}")


def sync_flunet() -> None:
    run_script("sync_flunet.py", ["--from-year", "2024"])


def sync_weather(countries: str | None = None) -> None:
    args = ["--weeks-back", "12"]
    if countries:
        args.extend(["--countries", countries])
    run_script("sync_weather.py", args)


def build_features() -> None:
    run_script("feature_builder.py", ["--disease", "flu", "--from-year", str(date.today().year)])


def batch_predict() -> None:
    run_script("batch_predict.py")


def run_once(countries: str | None = None) -> None:
    sync_flunet()
    sync_weather(countries=countries)
    build_features()
    batch_predict()


def main() -> None:
    parser = argparse.ArgumentParser(description="EpiWatch Docker scheduler worker")
    parser.add_argument("--run-once", action="store_true",
                        help="Run the pipeline once immediately, then exit")
    parser.add_argument("--countries", type=str, default=None,
                        help="Optional comma-separated iso3 list for sync_weather smoke tests")
    args = parser.parse_args()

    if args.run_once:
        run_once(countries=args.countries)
        return

    scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(sync_flunet, CronTrigger(day_of_week="mon", hour=10, minute=0), id="sync_flunet")
    scheduler.add_job(sync_weather, CronTrigger(hour=6, minute=0), id="sync_weather")
    scheduler.add_job(build_features, CronTrigger(day_of_week="mon", hour=11, minute=0), id="build_features")
    scheduler.add_job(batch_predict, CronTrigger(day_of_week="mon", hour=11, minute=30), id="batch_predict")

    print("[scheduler] started", flush=True)
    scheduler.start()


if __name__ == "__main__":
    main()
