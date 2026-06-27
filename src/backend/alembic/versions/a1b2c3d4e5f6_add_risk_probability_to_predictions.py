"""add risk_probability to predictions

Revision ID: a1b2c3d4e5f6
Revises: cbd62e71217a
Create Date: 2026-05-24 12:00:00.000000

Thêm cột risk_probability lưu P(class thắng) từ XGBClassifier.predict_proba.
FE dùng giá trị này làm risk score (0..1 → 0..100) thay vì proxy cứng.
NULL = prediction cũ chưa có score; FE fallback hardcode mapping.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cbd62e71217a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'predictions',
        sa.Column('risk_probability', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('predictions', 'risk_probability')
