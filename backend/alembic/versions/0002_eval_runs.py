"""eval runs tables

Revision ID: 0002_eval_runs
Revises: 0001_initial_schema
Create Date: 2026-02-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_eval_runs"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("actor_user_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=64), nullable=False),
        sa.Column("total_cases", sa.Integer(), nullable=False),
        sa.Column("avg_clarity", sa.Float(), nullable=False),
        sa.Column("avg_tone_match", sa.Float(), nullable=False),
        sa.Column("avg_factuality", sa.Float(), nullable=False),
        sa.Column("avg_overall", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_eval_runs_run_id", "eval_runs", ["run_id"])
    op.create_index("ix_eval_runs_actor_user_id", "eval_runs", ["actor_user_id"])
    op.create_index("ix_eval_runs_created_at", "eval_runs", ["created_at"])

    op.create_table(
        "eval_run_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("eval_runs.run_id"), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("tone", sa.String(length=64), nullable=False),
        sa.Column("clarity", sa.Float(), nullable=False),
        sa.Column("tone_match", sa.Float(), nullable=False),
        sa.Column("factuality", sa.Float(), nullable=False),
        sa.Column("overall", sa.Float(), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=False),
    )
    op.create_index("ix_eval_run_items_run_id", "eval_run_items", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_eval_run_items_run_id", table_name="eval_run_items")
    op.drop_table("eval_run_items")
    op.drop_index("ix_eval_runs_created_at", table_name="eval_runs")
    op.drop_index("ix_eval_runs_actor_user_id", table_name="eval_runs")
    op.drop_index("ix_eval_runs_run_id", table_name="eval_runs")
    op.drop_table("eval_runs")
