"""increase_section_column_sizes

Revision ID: a1b2c3d4e5f6
Revises: c5c0d2eddcf3
Create Date: 2025-12-18 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c5c0d2eddcf3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase section column size from varchar(50) to varchar(255)
    op.alter_column(
        "legal_texts",
        "section",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
    # Increase sub_section column size from varchar(50) to varchar(255)
    op.alter_column(
        "legal_texts",
        "sub_section",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert sub_section column size to varchar(50)
    op.alter_column(
        "legal_texts",
        "sub_section",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
    # Revert section column size to varchar(50)
    op.alter_column(
        "legal_texts",
        "section",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
