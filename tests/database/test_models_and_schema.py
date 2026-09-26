"""Unit tests verifying SQLAlchemy models, schema constraints, indexes, and mixins."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import inspect
from backend.app.models import (
    Base,
    Role,
    User,
    Bank,
    Account,
    ATM,
    Transaction,
    Case,
    Complaint,
    Alert,
    AuditLog,
)


EXPECTED_TABLES = {
    "roles",
    "users",
    "banks",
    "accounts",
    "atms",
    "transactions",
    "cases",
    "complaints",
    "alerts",
    "audit_logs",
}


def test_all_ten_tables_registered_in_metadata():
    """Verify that all 10 required normalized tables are registered in Base.metadata."""
    registered_tables = set(Base.metadata.tables.keys())
    for table_name in EXPECTED_TABLES:
        assert table_name in registered_tables, f"Table {table_name} missing from Base.metadata"


def test_primary_keys_defined_across_all_tables():
    """Verify every table has a defined primary key."""
    for table_name in EXPECTED_TABLES:
        table = Base.metadata.tables[table_name]
        pk_columns = [col.name for col in table.primary_key.columns]
        assert len(pk_columns) >= 1, f"Table {table_name} does not have a primary key"
        assert "id" in pk_columns or "account_number" in pk_columns


def test_foreign_key_relationships_configured():
    """Verify foreign key constraints link dependent tables correctly."""
    users_table = Base.metadata.tables["users"]
    accounts_table = Base.metadata.tables["accounts"]
    atms_table = Base.metadata.tables["atms"]
    transactions_table = Base.metadata.tables["transactions"]
    complaints_table = Base.metadata.tables["complaints"]
    cases_table = Base.metadata.tables["cases"]
    alerts_table = Base.metadata.tables["alerts"]
    audit_logs_table = Base.metadata.tables["audit_logs"]

    # users.role_id -> roles.id
    user_fks = [fk.target_fullname for fk in users_table.foreign_keys]
    assert "roles.id" in user_fks

    # accounts.bank_id -> banks.id
    account_fks = [fk.target_fullname for fk in accounts_table.foreign_keys]
    assert "banks.id" in account_fks

    # atms.bank_id -> banks.id
    atm_fks = [fk.target_fullname for fk in atms_table.foreign_keys]
    assert "banks.id" in atm_fks

    # transactions -> accounts.id, atms.id
    txn_fks = [fk.target_fullname for fk in transactions_table.foreign_keys]
    assert "accounts.id" in txn_fks
    assert "atms.id" in txn_fks

    # complaints -> cases.id, accounts.id
    complaint_fks = [fk.target_fullname for fk in complaints_table.foreign_keys]
    assert "cases.id" in complaint_fks
    assert "accounts.id" in complaint_fks

    # cases -> users.id
    case_fks = [fk.target_fullname for fk in cases_table.foreign_keys]
    assert "users.id" in case_fks

    # alerts -> accounts.id, transactions.id, cases.id
    alert_fks = [fk.target_fullname for fk in alerts_table.foreign_keys]
    assert "accounts.id" in alert_fks
    assert "transactions.id" in alert_fks
    assert "cases.id" in alert_fks

    # audit_logs -> users.id
    audit_fks = [fk.target_fullname for fk in audit_logs_table.foreign_keys]
    assert "users.id" in audit_fks


def test_indexes_defined_on_search_and_fk_columns():
    """Verify indexes are created on critical identifier, timestamp, and status columns."""
    for table_name in ["users", "accounts", "transactions", "complaints", "alerts", "cases"]:
        table = Base.metadata.tables[table_name]
        index_names = [idx.name for idx in table.indexes]
        assert len(index_names) > 0, f"Table {table_name} should have indexed columns"


def test_timestamp_mixin_defaults():
    """Verify TimestampMixin initializes created_at and updated_at."""
    role = Role(name="test_role", description="Test role description", permissions=["test"])
    assert role.created_at is not None
    assert role.updated_at is not None


def test_soft_delete_mixin_behavior():
    """Verify SoftDeleteMixin soft_delete() and restore() lifecycle."""
    bank = Bank(bank_code="TSTB", bank_name="Test Bank")
    assert bank.is_deleted is False
    assert bank.deleted_at is None

    # Soft delete
    bank.soft_delete()
    assert bank.is_deleted is True
    assert bank.deleted_at is not None
    assert isinstance(bank.deleted_at, datetime)

    # Restore
    bank.restore()
    assert bank.is_deleted is False
    assert bank.deleted_at is None
