"""Case management workflow, notes, evidence, timeline, and resolution.

Revision ID: 0002_case_management_workflow
Revises: 0001_initial_schema
Create Date: 2026-09-26 20:15:00.000000

Adds:
- cases table extensions (alert_id, assigned_investigator, timestamps, resolution fields)
- case_notes table
- case_evidence table
- case_timeline_events table
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_case_management_workflow"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. EXTEND CASES TABLE
    op.add_column("cases", sa.Column("alert_id", sa.String(length=50), nullable=True))
    op.add_column("cases", sa.Column("assigned_investigator", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("assigned_by", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("created_by_username", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("resolved_by", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("resolution_status", sa.String(length=50), nullable=True))
    op.add_column("cases", sa.Column("resolution_category", sa.String(length=50), nullable=True))
    op.add_column("cases", sa.Column("resolution_reason", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("resolution_notes", sa.Text(), nullable=True))
    op.add_column("cases", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("closed_by", sa.String(length=255), nullable=True))

    op.create_index("ix_cases_alert_id", "cases", ["alert_id"])
    op.create_index("ix_cases_assigned_investigator", "cases", ["assigned_investigator"])
    op.create_index("ix_cases_resolution_status", "cases", ["resolution_status"])

    # 2. CASE NOTES TABLE
    op.create_table(
        "case_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.String(length=255), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("author_role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])
    op.create_index("ix_case_notes_created_at", "case_notes", ["created_at"])

    # 3. CASE EVIDENCE TABLE
    op.create_table(
        "case_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("evidence_reference_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("added_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_evidence_case_id", "case_evidence", ["case_id"])
    op.create_index("ix_case_evidence_evidence_type", "case_evidence", ["evidence_type"])
    op.create_index("ix_case_evidence_reference_id", "case_evidence", ["evidence_reference_id"])

    # 4. CASE TIMELINE EVENTS TABLE
    op.create_table(
        "case_timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=50), server_default="INVESTIGATOR", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_case_timeline_case_id", "case_timeline_events", ["case_id"])
    op.create_index("ix_case_timeline_event_type", "case_timeline_events", ["event_type"])
    op.create_index("ix_case_timeline_timestamp", "case_timeline_events", ["timestamp"])


def downgrade() -> None:
    op.drop_table("case_timeline_events")
    op.drop_table("case_evidence")
    op.drop_table("case_notes")
    op.drop_index("ix_cases_resolution_status", table_name="cases")
    op.drop_index("ix_cases_assigned_investigator", table_name="cases")
    op.drop_index("ix_cases_alert_id", table_name="cases")
    op.drop_column("cases", "closed_by")
    op.drop_column("cases", "closed_at")
    op.drop_column("cases", "resolution_notes")
    op.drop_column("cases", "resolution_reason")
    op.drop_column("cases", "resolution_category")
    op.drop_column("cases", "resolution_status")
    op.drop_column("cases", "resolved_by")
    op.drop_column("cases", "resolved_at")
    op.drop_column("cases", "created_by_username")
    op.drop_column("cases", "assigned_by")
    op.drop_column("cases", "assigned_at")
    op.drop_column("cases", "assigned_investigator")
    op.drop_column("cases", "alert_id")
