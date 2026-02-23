"""add thread_memories table

Revision ID: 0005_thread_memories
Revises: 0004_user_password_hash
Create Date: 2026-02-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_thread_memories"
down_revision: Union[str, None] = "0004_user_password_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "thread_memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("tone", sa.String(length=64), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("draft_text", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_thread_memories_thread_id"), "thread_memories", ["thread_id"], unique=False)
    op.create_index(op.f("ix_thread_memories_user_id"), "thread_memories", ["user_id"], unique=False)
    op.create_index(op.f("ix_thread_memories_created_at"), "thread_memories", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_thread_memories_created_at"), table_name="thread_memories")
    op.drop_index(op.f("ix_thread_memories_user_id"), table_name="thread_memories")
    op.drop_index(op.f("ix_thread_memories_thread_id"), table_name="thread_memories")
    op.drop_table("thread_memories")

