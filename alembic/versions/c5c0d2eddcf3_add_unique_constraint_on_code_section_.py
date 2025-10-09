"""add_unique_constraint_on_code_section_subsection

Revision ID: c5c0d2eddcf3
Revises: 856529c86a85
Create Date: 2025-10-08 20:23:14.513094

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c5c0d2eddcf3"
down_revision: Union[str, Sequence[str], None] = "856529c86a85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create unique constraint on code, section, and sub_section combination
    op.create_unique_constraint(
        "uq_legal_texts_code_section_subsection",
        "legal_texts",
        ["code", "section", "sub_section"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique constraint
    op.drop_constraint(
        "uq_legal_texts_code_section_subsection", "legal_texts", type_="unique"
    )
