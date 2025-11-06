"""merge_migration_heads

Revision ID: e0abfab9cacb
Revises: 8efe2bdd52c0, align_schemas_v1
Create Date: 2025-11-06 06:53:47.185576

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'e0abfab9cacb'
down_revision = ('8efe2bdd52c0', 'align_schemas_v1')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass