"""add source_id to disease_cases

Revision ID: f6a7b8c9d0e1
Revises: d4e5f6a7b8c9
Create Date: 2026-06-30 10:00:00.000000

Thêm cột source_id (FK → data_sources.id) vào bảng disease_cases để truy vết
xuất xứ từng bản ghi ca bệnh (FluNet, OpenDengue, ECDC...). Nullable vì các
bản ghi lịch sử đã load trước khi có cột này.

Lưu ý: disease_cases là bảng phân vùng (PARTITION BY RANGE iso_year).
ALTER TABLE trên bảng cha tự động áp dụng cho tất cả partition con.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "disease_cases",
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("data_sources.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "disease_cases_source_id_fkey",
        "disease_cases",
        type_="foreignkey",
    )
    op.drop_column("disease_cases", "source_id")
