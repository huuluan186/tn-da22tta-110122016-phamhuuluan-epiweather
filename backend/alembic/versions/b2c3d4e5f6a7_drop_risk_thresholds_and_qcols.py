"""drop risk_thresholds table and legacy q33/q67 columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-17 00:00:00.000000

Gỡ bỏ phương pháp phân vị q33/q67 (Nhánh A cũ) khỏi DB. Phân loại rủi ro
production lấy trực tiếp từ XGBClassifier (nhãn endemic channel Bortman 1999),
nên bảng risk_thresholds và hai cột predictions.risk_q33/risk_q67 chỉ còn là
metadata chết, dễ gây hiểu nhầm là hệ thống dùng percentile. Drop hẳn để sạch.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('predictions', 'risk_q33')
    op.drop_column('predictions', 'risk_q67')
    op.drop_table('risk_thresholds')


def downgrade() -> None:
    op.create_table(
        'risk_thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('disease_id', sa.Integer(), nullable=False),
        sa.Column('iso3', sa.String(length=10), nullable=False),
        sa.Column('q33', sa.Float(), nullable=False),
        sa.Column('q67', sa.Float(), nullable=False),
        sa.Column('n_nonzero_weeks', sa.Integer(), nullable=True),
        sa.Column('is_global_fallback', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('model_version_id', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['disease_id'], ['diseases.id']),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('disease_id', 'iso3'),
    )
    op.add_column('predictions', sa.Column('risk_q67', sa.Float(), nullable=True))
    op.add_column('predictions', sa.Column('risk_q33', sa.Float(), nullable=True))
