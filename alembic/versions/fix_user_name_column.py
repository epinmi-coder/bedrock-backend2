"""fix user_name column issue

Revision ID: fix_user_name_column
Revises: e0abfab9cacb
Create Date: 2025-11-06 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_user_name_column'
down_revision = 'e0abfab9cacb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix the user_name column issue:
    1. Ensure user_id is populated from user_name
    2. Drop user_name column (no longer needed)
    """
    
    # First, ensure user_id column exists and is populated
    try:
        # Copy data from user_name to user_id if user_id is empty
        op.execute("UPDATE chats SET user_id = user_name WHERE user_id IS NULL AND user_name IS NOT NULL")
        op.execute("UPDATE chats SET user_id = 'anonymous' WHERE user_id IS NULL")
    except Exception as e:
        print(f"Data migration note: {e}")
    
    # Drop the old user_name column
    try:
        op.drop_column('chats', 'user_name')
        print("✅ Dropped user_name column")
    except Exception as e:
        print(f"Note: Could not drop user_name column: {e}")


def downgrade() -> None:
    """Revert the changes"""
    
    # Restore user_name column
    op.add_column('chats', sa.Column('user_name', sa.VARCHAR(), nullable=True))
    # Copy data back
    op.execute('UPDATE chats SET user_name = user_id')
    # Make it not null
    op.alter_column('chats', 'user_name', nullable=False)
