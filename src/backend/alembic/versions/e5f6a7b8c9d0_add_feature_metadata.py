"""add feature metadata

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-12 13:00:00.000000

Them ten hien thi va mo ta tieng Viet cho catalog feature.
Metadata production duoc seed bang scripts/db_migrate_feature_metadata.sql.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE feature_configs
            ADD COLUMN IF NOT EXISTS display_name_vi VARCHAR(150),
            ADD COLUMN IF NOT EXISTS description_vi VARCHAR(500)
        """
    )


def downgrade() -> None:
    op.drop_column("feature_configs", "description_vi")
    op.drop_column("feature_configs", "display_name_vi")
