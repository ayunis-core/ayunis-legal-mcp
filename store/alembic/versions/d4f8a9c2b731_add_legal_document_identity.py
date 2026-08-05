"""add legal document source and jurisdiction identity

Revision ID: d4f8a9c2b731
Revises: a1b2c3d4e5f6
Create Date: 2026-08-05 21:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f8a9c2b731"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_UNIQUE = "uq_legal_texts_code_section_subsection"
DOCUMENT_UNIQUE = "uq_legal_texts_document_section_subsection"


def upgrade() -> None:
    """Add document identity, backfill federal rows, and change uniqueness."""
    op.add_column("legal_texts", sa.Column("source", sa.String(100), nullable=True))
    op.add_column(
        "legal_texts", sa.Column("jurisdiction", sa.String(20), nullable=True)
    )
    op.add_column(
        "legal_texts", sa.Column("document_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "legal_texts", sa.Column("document_title", sa.String(512), nullable=True)
    )
    op.add_column(
        "legal_texts", sa.Column("document_type", sa.String(100), nullable=True)
    )
    op.add_column("legal_texts", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("legal_texts", sa.Column("build_date", sa.Date(), nullable=True))
    op.add_column("legal_texts", sa.Column("valid_from", sa.Date(), nullable=True))
    op.add_column("legal_texts", sa.Column("valid_to", sa.Date(), nullable=True))
    op.add_column(
        "legal_texts", sa.Column("content_hash", sa.String(64), nullable=True)
    )

    # Existing rows all came from this source and use the URL slug as `code`.
    # PostgreSQL's built-in md5 is sufficient for the one-time backfill; the next
    # shared import replaces it with the service's SHA-256 value.
    op.execute(
        """
        UPDATE legal_texts
        SET source = 'gesetze-im-internet',
            jurisdiction = 'DE',
            document_id = code,
            document_title = code,
            source_url = 'https://www.gesetze-im-internet.de/' || code || '/xml.zip',
            content_hash = md5(text)
        """
    )

    op.alter_column("legal_texts", "source", nullable=False)
    op.alter_column("legal_texts", "jurisdiction", nullable=False)
    op.alter_column("legal_texts", "document_id", nullable=False)
    op.alter_column("legal_texts", "document_title", nullable=False)
    op.alter_column("legal_texts", "content_hash", nullable=False)

    op.drop_constraint(OLD_UNIQUE, "legal_texts", type_="unique")
    op.create_unique_constraint(
        DOCUMENT_UNIQUE,
        "legal_texts",
        ["source", "jurisdiction", "document_id", "section", "sub_section"],
    )
    op.create_index("ix_legal_texts_source", "legal_texts", ["source"])
    op.create_index(
        "ix_legal_texts_jurisdiction", "legal_texts", ["jurisdiction"]
    )
    op.create_index("ix_legal_texts_document_id", "legal_texts", ["document_id"])


def downgrade() -> None:
    """Restore the federal-only schema without deleting any rows."""
    op.drop_index("ix_legal_texts_document_id", table_name="legal_texts")
    op.drop_index("ix_legal_texts_jurisdiction", table_name="legal_texts")
    op.drop_index("ix_legal_texts_source", table_name="legal_texts")
    op.drop_constraint(DOCUMENT_UNIQUE, "legal_texts", type_="unique")
    # This deliberately fails rather than discarding data if post-upgrade rows
    # collide under the legacy federal-only key.
    op.create_unique_constraint(
        OLD_UNIQUE,
        "legal_texts",
        ["code", "section", "sub_section"],
    )

    op.drop_column("legal_texts", "content_hash")
    op.drop_column("legal_texts", "valid_to")
    op.drop_column("legal_texts", "valid_from")
    op.drop_column("legal_texts", "build_date")
    op.drop_column("legal_texts", "source_url")
    op.drop_column("legal_texts", "document_type")
    op.drop_column("legal_texts", "document_title")
    op.drop_column("legal_texts", "document_id")
    op.drop_column("legal_texts", "jurisdiction")
    op.drop_column("legal_texts", "source")
