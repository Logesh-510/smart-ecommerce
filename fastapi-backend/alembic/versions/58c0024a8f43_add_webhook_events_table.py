"""add webhook events table

Revision ID: 58c0024a8f43
Revises: 2c0436e2d3d4
Create Date: 2026-08-31 16:39:23.452749

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "58c0024a8f43"
down_revision: Union[str, Sequence[str], None] = "2c0436e2d3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create webhook_events table."""

    op.create_table(
        "webhook_events",

        sa.Column(
            "id",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "processed_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop webhook_events table."""

    op.drop_table("webhook_events")