"""add users.password_hash

Revision ID: 0004_user_password_hash
Revises: 0003_seed_voice_personas
Create Date: 2026-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_user_password_hash"
down_revision: Union[str, None] = "0003_seed_voice_personas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
