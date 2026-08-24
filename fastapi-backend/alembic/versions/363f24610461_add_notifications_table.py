"""add notifications table

Revision ID: 363f24610461
Revises: 80c8ca953388
Create Date: 2026-08-24 12:49:36.440421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '363f24610461'
down_revision: Union[str, Sequence[str], None] = '80c8ca953388'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read_status', sa.Boolean(), nullable=False),
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        op.f('ix_notifications_id'),
        'notifications',
        ['id'],
        unique=False
    )

    op.create_index(
        op.f('ix_notifications_user_id'),
        'notifications',
        ['user_id'],
        unique=False
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_notifications_user_id'),
        table_name='notifications'
    )

    op.drop_index(
        op.f('ix_notifications_id'),
        table_name='notifications'
    )

    op.drop_table('notifications')