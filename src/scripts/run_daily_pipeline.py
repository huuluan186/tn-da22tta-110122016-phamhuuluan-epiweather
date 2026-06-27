"""
run_daily_pipeline.py — Master script chạy 4 jobs tuần tự, dùng cho Windows Task Scheduler.

Chạy hàng ngày 00:00 ICT (cấu hình qua Task Scheduler — không phụ thuộc FastAPI):
  1. sync_flunet      (WHO chỉ publish thứ Hai, các ngày khác trả 0 row mới — vô hại)
  2. sync_weather     (Open-Meteo cập nhật daily)
  3. build_features   (flu + dengue, năm hiện tại)
  4. batch_predict    (predict tuần mới nhất → predictions table)

Mỗi job tự log run riêng vào bảng pipeline_runs (trigger_type='scheduled').
Master script này KHÔNG ghi log riêng — chỉ chain.

Nếu một job fail, các job sau vẫn chạy (best-effort daily refresh).

Output:
  - stdout/stderr ghi vào logs/daily_pipeline_<date>.log (do Task Scheduler redirect)
  - DB rows ở pipeline_runs cho audit trail
"""
import datetime
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)


def run(name: str, args: list[str]) -> int:
    """Chạy 1 script với --trigger scheduled, return exit code (0 = OK)."""
    cmd = [str(PYTHON_EXE), str(SCRIPTS_DIR / name)] + args + ["--trigger", "scheduled"]
    print(f"\n{'='*70}\n>>> [{datetime.datetime.now():%H:%M:%S}] {name} {' '.join(args)}\n{'='*70}")
    proc = subprocess.run(cmd, timeout=3600)  # 1 hour timeout per job
    print(f">>> {name} exited rc={proc.returncode}")
    return proc.returncode


def main():
    started = datetime.datetime.now()
    print(f"╔══ EpiWatch daily pipeline ══ {started:%Y-%m-%d %H:%M:%S} ══╗")
    print(f"  Python: {PYTHON_EXE}")
    print(f"  Project: {PROJECT_ROOT}")

    cur_year = str(started.year)
    results = {}

    # 1) sync_flunet — pull 2024+
    results["sync_flunet"] = run("sync_flunet.py", ["--from-year", "2024"])

    # 2) sync_weather — 12 tuần gần nhất
    results["sync_weather"] = run("sync_weather.py", ["--weeks-back", "12"])

    # 3) build_features — flu + dengue năm hiện tại
    results["build_features_flu"] = run("feature_builder.py",
                                        ["--disease", "flu", "--from-year", cur_year])
    results["build_features_dengue"] = run("feature_builder.py",
                                           ["--disease", "dengue", "--from-year", cur_year])

    # 4) batch_predict — tuần mới nhất
    results["batch_predict"] = run("batch_predict.py", [])

    finished = datetime.datetime.now()
    elapsed = (finished - started).total_seconds()

    print(f"\n╔══ Done in {elapsed:.0f}s — {finished:%H:%M:%S} ══╗")
    for job, rc in results.items():
        status = "OK" if rc == 0 else f"FAIL (rc={rc})"
        print(f"  {job:<28} {status}")

    # Exit code: 0 nếu tất cả OK, 1 nếu có ít nhất 1 fail
    return 0 if all(rc == 0 for rc in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
