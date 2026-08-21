"""add payment status to orders

Revision ID: 80c8ca953388
Revises: 240973d28cd2
Create Date: 2026-08-20 10:27:05.921027

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "80c8ca953388"
down_revision: Union[str, Sequence[str], None] = "240973d28cd2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "orders",
        sa.Column(
            "payment_status",
            sa.String(),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "payment_status")