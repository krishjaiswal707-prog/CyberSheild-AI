"""Initial migration — create all tables

Revision ID: 001
Revises: 
Create Date: 2025-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── scam_analyses ──────────────────────────────────────────────────────────
    op.create_table(
        "scam_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False, index=True),
        sa.Column("analysis_type", sa.String(20), nullable=False),
        sa.Column("input_text", sa.Text, nullable=False),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("risk_score", sa.Integer, nullable=False),
        sa.Column("risk_tier", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("matched_red_flags", postgresql.JSON, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("rule_fired", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_scam_analyses_user_id", "scam_analyses", ["user_id"])

    # ── ncrb_complaints ────────────────────────────────────────────────────────
    op.create_table(
        "ncrb_complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("amount", sa.String(50), nullable=True),
        sa.Column("incident_timestamp", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("scam_type", sa.String(100), nullable=True),
        sa.Column("reference_number", sa.String(50), nullable=True),
        sa.Column("submitted", sa.Boolean, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ncrb_complaints_user_id", "ncrb_complaints", ["user_id"])

    # ── known_scammers ─────────────────────────────────────────────────────────
    op.create_table(
        "known_scammers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("identifier", sa.String(100), nullable=False),
        sa.Column("identifier_type", sa.String(20), nullable=False),
        sa.Column("report_count", sa.Integer, server_default="1"),
        sa.Column("scam_type", sa.String(100), nullable=False),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("last_reported", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_known_scammers_identifier", "known_scammers", ["identifier"])

    # ── scam_reports ───────────────────────────────────────────────────────────
    op.create_table(
        "scam_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("report_text", sa.Text, nullable=False),
        sa.Column("scam_type", sa.String(100), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("cluster_id", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_scam_reports_user_id", "scam_reports", ["user_id"])

    # ── user_sessions ──────────────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False, unique=True),
        sa.Column("whatsapp_number", sa.String(20), nullable=True),
        sa.Column("state", sa.String(50), server_default="idle"),
        sa.Column("last_analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("scam_reports")
    op.drop_table("known_scammers")
    op.drop_table("ncrb_complaints")
    op.drop_table("scam_analyses")
