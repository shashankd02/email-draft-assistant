"""add draft language and input mode telemetry

Revision ID: 0007_draft_input_telemetry
Revises: 0006_pub_threads_voice_tx
Create Date: 2026-02-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_draft_input_telemetry"
down_revision: Union[str, None] = "0006_pub_threads_voice_tx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drafts", sa.Column("language", sa.String(length=16), nullable=False, server_default="en"))
    op.add_column("drafts", sa.Column("input_mode", sa.String(length=16), nullable=False, server_default="text"))


def downgrade() -> None:
    op.drop_column("drafts", "input_mode")
    op.drop_column("drafts", "language")
