"""add disease localization

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-06-12 12:00:00.000000

Them ten va mo ta tieng Viet cho catalog benh de frontend lay tu API.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE diseases
            ADD COLUMN IF NOT EXISTS display_name_vi VARCHAR(100),
            ADD COLUMN IF NOT EXISTS description_vi TEXT
        """
    )
    op.execute(
        """
        UPDATE diseases
        SET display_name_vi = 'Cúm mùa',
            description_vi = 'Bệnh hô hấp theo mùa, lây qua giọt bắn và tiếp xúc gần.'
        WHERE code = 'flu'
        """
    )
    op.execute(
        """
        UPDATE diseases
        SET display_name_vi = 'Sốt xuất huyết Dengue',
            description_vi = 'Bệnh do muỗi truyền, bùng phát mạnh theo mùa mưa và khí hậu nóng ẩm.'
        WHERE code = 'dengue'
        """
    )


def downgrade() -> None:
    op.drop_column("diseases", "description_vi")
    op.drop_column("diseases", "display_name_vi")
