"""add public thread flag and voice transcripts

Revision ID: 0006_pub_threads_voice_tx
Revises: 0005_thread_memories
Create Date: 2026-02-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_pub_threads_voice_tx"
down_revision: Union[str, None] = "0005_thread_memories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("thread_memories", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index(op.f("ix_thread_memories_is_public"), "thread_memories", ["is_public"], unique=False)

    op.create_table(
        "voice_transcripts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_voice_transcripts_request_id"), "voice_transcripts", ["request_id"], unique=False)
    op.create_index(op.f("ix_voice_transcripts_user_id"), "voice_transcripts", ["user_id"], unique=False)
    op.create_index(op.f("ix_voice_transcripts_created_at"), "voice_transcripts", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_voice_transcripts_created_at"), table_name="voice_transcripts")
    op.drop_index(op.f("ix_voice_transcripts_user_id"), table_name="voice_transcripts")
    op.drop_index(op.f("ix_voice_transcripts_request_id"), table_name="voice_transcripts")
    op.drop_table("voice_transcripts")

    op.drop_index(op.f("ix_thread_memories_is_public"), table_name="thread_memories")
    op.drop_column("thread_memories", "is_public")
