"""add is_active to users

Revision ID: 2c0436e2d3d4
Revises: 363f24610461
Create Date: 2026-08-27 13:21:44.362856

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2c0436e2d3d4"
down_revision: Union[str, Sequence[str], None] = "363f24610461"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_active")