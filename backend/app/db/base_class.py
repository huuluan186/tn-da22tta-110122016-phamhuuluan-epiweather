"""Re-export Base cho code mới import từ db.base_class.

Base hiện đang định nghĩa trong app.models.geography (lý do lịch sử).
Module này tồn tại để code mới có thể `from app.db.base_class import Base`
và tránh circular imports khi refactor.
"""

from app.models.geography import Base

__all__ = ["Base"]
