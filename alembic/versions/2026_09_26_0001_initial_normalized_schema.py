"""Initial normalized PostgreSQL schema for cybercrime intelligence platform.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-26 12:35:00.000000

Normalized tables:
- roles
- users
- banks
- accounts
- atms
- cases
- complaints
- transactions
- alerts
- audit_logs
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ROLES
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("permissions", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_index("ix_roles_is_deleted", "roles", ["is_deleted"])

    # 2. USERS
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("badge_number", sa.String(length=100), nullable=True),
        sa.Column("department", sa.String(length=150), server_default="Cyber Crime Cell / LEA", nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_badge_number", "users", ["badge_number"])
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])

    # 3. BANKS
    op.create_table(
        "banks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bank_code", sa.String(length=10), nullable=False),
        sa.Column("bank_name", sa.String(length=150), nullable=False),
        sa.Column("bank_type", sa.String(length=50), server_default="Commercial", nullable=False),
        sa.Column("headquarters", sa.String(length=150), nullable=True),
        sa.Column("nodal_officer_name", sa.String(length=255), nullable=True),
        sa.Column("nodal_officer_email", sa.String(length=255), nullable=True),
        sa.Column("nodal_officer_phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_banks_bank_code", "banks", ["bank_code"], unique=True)
    op.create_index("ix_banks_bank_name", "banks", ["bank_name"])
    op.create_index("ix_banks_is_active", "banks", ["is_active"])
    op.create_index("ix_banks_is_deleted", "banks", ["is_deleted"])

    # 4. ACCOUNTS
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_number", sa.String(length=50), nullable=False),
        sa.Column("bank_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("banks.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("bank_name", sa.String(length=150), nullable=False),
        sa.Column("ifsc_code", sa.String(length=20), nullable=False),
        sa.Column("branch_name", sa.String(length=150), nullable=True),
        sa.Column("customer_id", sa.String(length=50), nullable=True),
        sa.Column("holder_name", sa.String(length=255), nullable=False),
        sa.Column("phone_linked", sa.String(length=20), nullable=True),
        sa.Column("account_type", sa.String(length=50), server_default="SAVINGS", nullable=False),
        sa.Column("balance_inr", sa.Numeric(precision=18, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("total_credit_volume_inr", sa.Numeric(precision=18, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("total_debit_volume_inr", sa.Numeric(precision=18, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("is_frozen", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=4), server_default=sa.text("0.0000"), nullable=False),
        sa.Column("mule_layer_detected", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("flagged_reasons", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_accounts_account_number", "accounts", ["account_number"], unique=True)
    op.create_index("ix_accounts_bank_id", "accounts", ["bank_id"])
    op.create_index("ix_accounts_bank_name", "accounts", ["bank_name"])
    op.create_index("ix_accounts_ifsc_code", "accounts", ["ifsc_code"])
    op.create_index("ix_accounts_customer_id", "accounts", ["customer_id"])
    op.create_index("ix_accounts_phone_linked", "accounts", ["phone_linked"])
    op.create_index("ix_accounts_is_frozen", "accounts", ["is_frozen"])
    op.create_index("ix_accounts_risk_score", "accounts", ["risk_score"])
    op.create_index("ix_accounts_mule_layer_detected", "accounts", ["mule_layer_detected"])
    op.create_index("ix_accounts_is_deleted", "accounts", ["is_deleted"])

    # 5. ATMS
    op.create_table(
        "atms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("atm_id", sa.String(length=50), nullable=False),
        sa.Column("bank_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("banks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("terminal_model", sa.String(length=100), nullable=True),
        sa.Column("location_id", sa.String(length=50), nullable=True),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_atms_atm_id", "atms", ["atm_id"], unique=True)
    op.create_index("ix_atms_bank_id", "atms", ["bank_id"])
    op.create_index("ix_atms_location_id", "atms", ["location_id"])
    op.create_index("ix_atms_city", "atms", ["city"])
    op.create_index("ix_atms_state", "atms", ["state"])
    op.create_index("ix_atms_pincode", "atms", ["pincode"])
    op.create_index("ix_atms_is_active", "atms", ["is_active"])
    op.create_index("ix_atms_is_deleted", "atms", ["is_deleted"])

    # 6. CASES
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_number", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="ACTIVE", nullable=False),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("total_fraud_amount_inr", sa.Numeric(precision=18, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("recovered_amount_inr", sa.Numeric(precision=18, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cases_case_number", "cases", ["case_number"], unique=True)
    op.create_index("ix_cases_title", "cases", ["title"])
    op.create_index("ix_cases_priority", "cases", ["priority"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_assigned_to_user_id", "cases", ["assigned_to_user_id"])
    op.create_index("ix_cases_created_by_user_id", "cases", ["created_by_user_id"])
    op.create_index("ix_cases_is_deleted", "cases", ["is_deleted"])

    # 7. COMPLAINTS
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("acknowledgement_no", sa.String(length=100), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("subcategory", sa.String(length=150), nullable=True),
        sa.Column("victim_name", sa.String(length=255), nullable=True),
        sa.Column("victim_phone", sa.String(length=20), nullable=True),
        sa.Column("victim_state", sa.String(length=100), nullable=False),
        sa.Column("victim_district", sa.String(length=100), nullable=True),
        sa.Column("reported_loss_inr", sa.Numeric(precision=15, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("suspect_upi", sa.String(length=255), nullable=True),
        sa.Column("suspect_account_number", sa.String(length=50), nullable=True),
        sa.Column("suspect_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suspect_ifsc", sa.String(length=20), nullable=True),
        sa.Column("suspect_phone", sa.String(length=20), nullable=True),
        sa.Column("incident_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reported_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="NEW", nullable=False),
        sa.Column("triage_priority", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=4), server_default=sa.text("0.0000"), nullable=False),
        sa.Column("description_synthetic", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_complaints_acknowledgement_no", "complaints", ["acknowledgement_no"], unique=True)
    op.create_index("ix_complaints_case_id", "complaints", ["case_id"])
    op.create_index("ix_complaints_category", "complaints", ["category"])
    op.create_index("ix_complaints_victim_phone", "complaints", ["victim_phone"])
    op.create_index("ix_complaints_victim_state", "complaints", ["victim_state"])
    op.create_index("ix_complaints_reported_loss_inr", "complaints", ["reported_loss_inr"])
    op.create_index("ix_complaints_suspect_upi", "complaints", ["suspect_upi"])
    op.create_index("ix_complaints_suspect_account_number", "complaints", ["suspect_account_number"])
    op.create_index("ix_complaints_suspect_account_id", "complaints", ["suspect_account_id"])
    op.create_index("ix_complaints_suspect_phone", "complaints", ["suspect_phone"])
    op.create_index("ix_complaints_incident_timestamp", "complaints", ["incident_timestamp"])
    op.create_index("ix_complaints_reported_timestamp", "complaints", ["reported_timestamp"])
    op.create_index("ix_complaints_status", "complaints", ["status"])
    op.create_index("ix_complaints_triage_priority", "complaints", ["triage_priority"])
    op.create_index("ix_complaints_risk_score", "complaints", ["risk_score"])
    op.create_index("ix_complaints_is_deleted", "complaints", ["is_deleted"])

    # 8. TRANSACTIONS
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("txn_ref_no", sa.String(length=100), nullable=False),
        sa.Column("sender_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("receiver_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sender_account_number", sa.String(length=50), nullable=True),
        sa.Column("receiver_account_number", sa.String(length=50), nullable=True),
        sa.Column("sender_upi", sa.String(length=255), nullable=True),
        sa.Column("receiver_upi", sa.String(length=255), nullable=True),
        sa.Column("sender_device_id", sa.String(length=100), nullable=True),
        sa.Column("receiver_device_id", sa.String(length=100), nullable=True),
        sa.Column("atm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("atms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_inr", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("rail_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="SUCCESS", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("layer_depth", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("is_flagged_suspicious", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("anomaly_score", sa.Numeric(precision=5, scale=4), server_default=sa.text("0.0000"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_transactions_txn_ref_no", "transactions", ["txn_ref_no"], unique=True)
    op.create_index("ix_transactions_sender_account_id", "transactions", ["sender_account_id"])
    op.create_index("ix_transactions_receiver_account_id", "transactions", ["receiver_account_id"])
    op.create_index("ix_transactions_sender_account_number", "transactions", ["sender_account_number"])
    op.create_index("ix_transactions_receiver_account_number", "transactions", ["receiver_account_number"])
    op.create_index("ix_transactions_sender_upi", "transactions", ["sender_upi"])
    op.create_index("ix_transactions_receiver_upi", "transactions", ["receiver_upi"])
    op.create_index("ix_transactions_atm_id", "transactions", ["atm_id"])
    op.create_index("ix_transactions_amount_inr", "transactions", ["amount_inr"])
    op.create_index("ix_transactions_rail_type", "transactions", ["rail_type"])
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_timestamp", "transactions", ["timestamp"])
    op.create_index("ix_transactions_layer_depth", "transactions", ["layer_depth"])
    op.create_index("ix_transactions_is_flagged_suspicious", "transactions", ["is_flagged_suspicious"])
    op.create_index("ix_transactions_anomaly_score", "transactions", ["anomaly_score"])

    # 9. ALERTS
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_id", sa.String(length=50), nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="OPEN", nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("triggered_entity_type", sa.String(length=50), nullable=False),
        sa.Column("triggered_entity_id", sa.String(length=100), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rule_flags", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_alert_id", "alerts", ["alert_id"], unique=True)
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_risk_score", "alerts", ["risk_score"])
    op.create_index("ix_alerts_triggered_entity_type", "alerts", ["triggered_entity_type"])
    op.create_index("ix_alerts_triggered_entity_id", "alerts", ["triggered_entity_id"])
    op.create_index("ix_alerts_account_id", "alerts", ["account_id"])
    op.create_index("ix_alerts_transaction_id", "alerts", ["transaction_id"])
    op.create_index("ix_alerts_case_id", "alerts", ["case_id"])

    # 10. AUDIT LOGS
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=False),
        sa.Column("details", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
        sa.Column("client_ip", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_table("transactions")
    op.drop_table("complaints")
    op.drop_table("cases")
    op.drop_table("atms")
    op.drop_table("accounts")
    op.drop_table("banks")
    op.drop_table("users")
    op.drop_table("roles")
