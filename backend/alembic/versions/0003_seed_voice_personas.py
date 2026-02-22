"""seed default voice personas

Revision ID: 0003_seed_voice_personas
Revises: 0002_eval_runs
Create Date: 2026-02-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_seed_voice_personas"
down_revision: Union[str, None] = "0002_eval_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    voice_personas = sa.table(
        "voice_personas",
        sa.column("name", sa.String(length=64)),
        sa.column("provider", sa.String(length=64)),
        sa.column("provider_voice_key", sa.String(length=128)),
        sa.column("active", sa.Boolean()),
    )
    op.bulk_insert(
        voice_personas,
        [
            {"name": "Professional", "provider": "openai", "provider_voice_key": "alloy", "active": True},
            {"name": "Casual", "provider": "openai", "provider_voice_key": "verse", "active": True},
            {"name": "Assertive", "provider": "openai", "provider_voice_key": "echo", "active": True},
            {"name": "Empathetic", "provider": "openai", "provider_voice_key": "shimmer", "active": True},
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM voice_personas WHERE name IN ('Professional','Casual','Assertive','Empathetic')")
