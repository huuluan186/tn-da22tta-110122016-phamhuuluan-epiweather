from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary():
    """Dashboard tổng hợp — placeholder, sẽ implement ở Phase 8."""
    return {"message": "Analytics endpoint — coming soon"}
