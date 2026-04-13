"""create session metadata table

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 00:01:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260412_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "session_metadata",
        sa.Column("session_id_hash", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "IDLE",
                "ACTIVE",
                "DEGRADED",
                "CLOSING",
                "CLOSED",
                "ERROR",
                name="sessionstate",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("session_metadata")
