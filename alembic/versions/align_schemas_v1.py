"""align schemas with frontend expectations

Revision ID: align_schemas_v1
Revises: 
Create Date: 2025-11-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'align_schemas_v1'
down_revision = None  # Update this with your last migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Align database schema with frontend expectations:
    1. Add message_uid and response_session_id columns
    2. Add user_id column
    3. Rename bedrock_response to response
    4. Add indexes for performance
    """
    
    # Add new UUID columns
    op.add_column('chats', sa.Column('message_uid', postgresql.UUID(), nullable=True))
    op.add_column('chats', sa.Column('response_session_id', postgresql.UUID(), nullable=True))
    
    # Add user_id column (temporarily nullable for migration)
    op.add_column('chats', sa.Column('user_id', sa.VARCHAR(length=255), nullable=True))
    
    # Migrate data from user_name to user_id if user_name exists
    try:
        op.execute('UPDATE chats SET user_id = user_name WHERE user_id IS NULL')
    except:
        # If user_name doesn't exist, set default value
        op.execute("UPDATE chats SET user_id = 'anonymous' WHERE user_id IS NULL")
    
    # Make user_id not null after migration
    op.alter_column('chats', 'user_id', nullable=False)
    
    # Rename bedrock_response to response
    op.alter_column('chats', 'bedrock_response', new_column_name='response')
    
    # Add indexes for better query performance
    op.create_index('idx_chats_message_uid', 'chats', ['message_uid'], unique=False)
    op.create_index('idx_chats_user_id', 'chats', ['user_id'], unique=False)
    
    # Optional: Drop user_name column if it exists (uncomment if needed)
    # try:
    #     op.drop_column('chats', 'user_name')
    # except:
    #     pass


def downgrade() -> None:
    """Revert the schema changes"""
    
    # Drop indexes
    op.drop_index('idx_chats_user_id', table_name='chats')
    op.drop_index('idx_chats_message_uid', table_name='chats')
    
    # Rename response back to bedrock_response
    op.alter_column('chats', 'response', new_column_name='bedrock_response')
    
    # Restore user_name column if needed
    # op.add_column('chats', sa.Column('user_name', sa.VARCHAR(), nullable=True))
    # op.execute('UPDATE chats SET user_name = user_id')
    
    # Drop new columns
    op.drop_column('chats', 'user_id')
    op.drop_column('chats', 'response_session_id')
    op.drop_column('chats', 'message_uid')
