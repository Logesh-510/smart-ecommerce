"""fix cart schema

Revision ID: 240973d28cd2
Revises: 4056f01a563d
Create Date: 2026-08-19 13:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "240973d28cd2"
down_revision: Union[str, Sequence[str], None] = "4056f01a563d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Remove old cart columns.
    op.drop_constraint(
        "carts_product_id_fkey",
        "carts",
        type_="foreignkey",
    )

    op.drop_constraint(
        "carts_user_id_fkey",
        "carts",
        type_="foreignkey",
    )

    op.drop_column("carts", "product_id")
    op.drop_column("carts", "quantity")

    # Make each user have only one cart.
    op.create_unique_constraint(
        "uq_carts_user_id",
        "carts",
        ["user_id"],
    )

    # Create cart items table.
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["carts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_cart_items_id"),
        "cart_items",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_cart_items_id"),
        table_name="cart_items",
    )

    op.drop_table("cart_items")

    op.drop_constraint(
        "uq_carts_user_id",
        "carts",
        type_="unique",
    )

    op.add_column(
        "carts",
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.add_column(
        "carts",
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False,
        ),
    )

    op.create_foreign_key(
        "carts_product_id_fkey",
        "carts",
        "products",
        ["product_id"],
        ["id"],
    )

    op.create_foreign_key(
        "carts_user_id_fkey",
        "carts",
        "users",
        ["user_id"],
        ["id"],
    )