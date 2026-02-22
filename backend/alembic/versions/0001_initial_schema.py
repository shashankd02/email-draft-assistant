"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voice_personas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_voice_key", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("default_voice_id", sa.Integer(), sa.ForeignKey("voice_personas.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("preferred_tone", sa.String(length=32), nullable=True),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("prefs_json", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "drafts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("tone", sa.String(length=64), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("request_id", name="uq_drafts_request_id"),
    )
    op.create_index("ix_drafts_user_created", "drafts", ["user_id", "created_at"])

    op.create_table(
        "judge_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("draft_id", sa.String(length=64), sa.ForeignKey("drafts.id"), nullable=False),
        sa.Column("clarity", sa.Float(), nullable=False),
        sa.Column("tone_match", sa.Float(), nullable=False),
        sa.Column("factuality", sa.Float(), nullable=False),
        sa.Column("overall", sa.Float(), nullable=False),
        sa.Column("judge_model", sa.String(length=128), nullable=False, server_default="gpt-4o"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "tool_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("payload_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_tool_events_request_tool", "tool_events", ["request_id", "tool_name"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("actor_user_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=True),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_audit_logs_request_created", "audit_logs", ["request_id", "created_at"])

    op.create_table(
        "feedback_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("draft_id", sa.String(length=64), sa.ForeignKey("drafts.id"), nullable=False),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("feedback_tags", sa.Text(), nullable=True),
        sa.Column("diff_ratio", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("feedback_events")
    op.drop_index("ix_audit_logs_request_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_tool_events_request_tool", table_name="tool_events")
    op.drop_table("tool_events")
    op.drop_table("judge_scores")
    op.drop_index("ix_drafts_user_created", table_name="drafts")
    op.drop_table("drafts")
    op.drop_table("user_profiles")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")
    op.drop_table("voice_personas")
