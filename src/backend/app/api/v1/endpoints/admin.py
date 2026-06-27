"""Admin endpoints — trigger manual sync, xem scheduler status."""

from fastapi import APIRouter, HTTPException

from ....services import scheduler

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/scheduler/status")
def scheduler_status():
    """Trả về tình trạng scheduler + danh sách jobs + next_run_time."""
    return scheduler.get_scheduler_status()


@router.post("/sync/{job_id}")
def sync_trigger(job_id: str):
    """
    Trigger ngay 1 sync job (không đợi cron).

    job_id options:
      sync_flunet                   — pull WHO FluNet data mới nhất
      sync_weather                  — pull Open-Meteo weather 12 tuần gần nhất
      build_features                — rebuild flu + dengue features năm hiện tại
      build_features_dengue_nowcast — rebuild dengue features 2020-2023 (sau khi load OpenDengue batch mới)
      batch_predict                 — predict tuần mới nhất → predictions table
    """
    valid = {
        "sync_flunet", "sync_weather",
        "build_features", "build_features_dengue_nowcast",
        "batch_predict",
    }
    if job_id not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"job_id phải là một trong: {sorted(valid)}",
        )
    result = scheduler.trigger_manual(job_id)
    if result.get("returncode", 0) != 0:
        raise HTTPException(status_code=500, detail=result)
    return {"job_id": job_id, "result": result}
