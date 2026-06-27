"""
scheduler.py — APScheduler cho auto-sync FluNet + Open-Meteo.

Jobs:
  - sync_flunet:      Thứ Hai 10:00 ICT (WHO publish weekly Monday)
  - sync_weather:     Hằng ngày 6:00 ICT (Open-Meteo cập nhật daily)
  - build_features:   Thứ Hai 11:00 ICT (sau flu sync, rebuild feature snapshots)
  - batch_predict:    Thứ Hai 11:30 ICT (sau build_features, predict → predictions table)

Trigger qua subprocess gọi scripts/*.py — không tích hợp logic trực tiếp
để giữ scripts standalone (dễ debug, dễ chạy manual).

Khi cần kích hoạt manual: POST /api/v1/admin/sync/{job_name}
"""

import subprocess
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# Project root → scripts/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"  # Windows venv
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path("python")  # fallback PATH


_scheduler: AsyncIOScheduler | None = None


def _run_script(name: str, extra_args: list[str] | None = None) -> dict:
    """Run script qua subprocess. Trả về {returncode, stdout_tail, stderr_tail}."""
    script = SCRIPTS_DIR / name
    if not script.exists():
        logger.error(f"[scheduler] Script không tồn tại: {script}")
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": "script not found"}

    cmd = [str(PYTHON_EXE), str(script)] + (extra_args or [])
    logger.info(f"[scheduler] Running: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min
        rc = proc.returncode
        stdout_tail = (proc.stdout or "")[-500:]
        stderr_tail = (proc.stderr or "")[-500:]
        if rc == 0:
            logger.info(f"[scheduler] {name} OK")
        else:
            logger.error(f"[scheduler] {name} failed rc={rc}: {stderr_tail}")
        return {"returncode": rc, "stdout_tail": stdout_tail, "stderr_tail": stderr_tail}
    except subprocess.TimeoutExpired:
        logger.error(f"[scheduler] {name} timed out (1800s)")
        return {"returncode": -2, "stdout_tail": "", "stderr_tail": "timeout"}


# ── Job functions ─────────────────────────────────────────────────────────────

def job_sync_flunet():
    """Pull WHO FluNet data từ 2024 đến hiện tại."""
    return _run_script("sync_flunet.py", ["--from-year", "2024"])


def job_sync_weather():
    """Pull Open-Meteo weather 12 tuần gần nhất."""
    return _run_script("sync_weather.py", ["--weeks-back", "12"])


def job_build_features():
    """Rebuild flu feature snapshots cho năm hiện tại (chạy sau sync).

    Dengue không có nguồn cập nhật hằng tuần kiểu FluNet. Không build dengue
    theo năm hiện tại vì sẽ sinh placeholder sau cutoff OpenDengue 2023-W36.
    Khi có batch OpenDengue mới, chạy riêng build_features_dengue_nowcast.
    """
    import datetime
    cur_year = str(datetime.date.today().year)
    r_flu = _run_script("feature_builder.py", ["--disease", "flu", "--from-year", cur_year])
    return {"returncode": r_flu["returncode"], "flu": r_flu}


def job_build_features_dengue_nowcast():
    """
    Rebuild dengue feature snapshots 2020-2023 thủ công.

    Trigger sau khi load batch mới từ OpenDengue.
    OpenDengue không có API realtime → chạy manual khi có release mới.
    """
    r = _run_script("feature_builder.py", [
        "--disease", "dengue", "--from-year", "2020", "--to-year", "2023"
    ])
    return r


def job_batch_predict():
    """Predict h=1 + classifier cho tất cả countries tuần mới nhất → predictions table."""
    return _run_script("batch_predict.py")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def init_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        logger.warning("[scheduler] Already initialized, skip")
        return

    _scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")

    # Thứ Hai 10:00 ICT — sync FluNet
    _scheduler.add_job(
        job_sync_flunet,
        CronTrigger(day_of_week="mon", hour=10, minute=0),
        id="sync_flunet",
        replace_existing=True,
    )

    # Hằng ngày 6:00 ICT — sync weather
    _scheduler.add_job(
        job_sync_weather,
        CronTrigger(hour=6, minute=0),
        id="sync_weather",
        replace_existing=True,
    )

    # Thứ Hai 11:00 ICT — rebuild features (sau khi flu sync lúc 10:00 xong)
    _scheduler.add_job(
        job_build_features,
        CronTrigger(day_of_week="mon", hour=11, minute=0),
        id="build_features",
        replace_existing=True,
    )

    # Thứ Hai 11:30 ICT — batch_predict (sau build_features)
    _scheduler.add_job(
        job_batch_predict,
        CronTrigger(day_of_week="mon", hour=11, minute=30),
        id="batch_predict",
        replace_existing=True,
    )

    _scheduler.start()
    jobs = _scheduler.get_jobs()
    logger.info(f"[scheduler] Started — {len(jobs)} jobs:")
    for j in jobs:
        logger.info(f"  - {j.id}: next run at {j.next_run_time}")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("[scheduler] Stopped")


def get_scheduler_status() -> dict:
    """Status hiện tại — dùng cho admin endpoint."""
    if _scheduler is None:
        return {"running": False, "jobs": []}
    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": j.id,
                "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
                "trigger": str(j.trigger),
            }
            for j in _scheduler.get_jobs()
        ],
    }


def trigger_manual(job_id: str) -> dict:
    """Trigger ngay 1 job — dùng cho admin endpoint."""
    if job_id == "sync_flunet":
        return job_sync_flunet()
    if job_id == "sync_weather":
        return job_sync_weather()
    if job_id == "build_features":
        return job_build_features()
    if job_id == "build_features_dengue_nowcast":
        return job_build_features_dengue_nowcast()
    if job_id == "batch_predict":
        return job_batch_predict()
    return {"returncode": -3, "stdout_tail": "", "stderr_tail": f"unknown job: {job_id}"}
