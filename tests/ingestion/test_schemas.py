"""Unit tests for Ingestion Event Schemas and mandatory envelope validation."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from ingestion.app.schemas import (
    AccountEvent,
    AlertEvent,
    ATMEvent,
    ComplaintEvent,
    IngestionEnvelope,
    TransactionEvent,
    BankEvent,
)


def test_mandatory_envelope_defaults():
    """Verify envelope generates required metadata attributes automatically."""
    envelope = IngestionEnvelope(source="TEST_SYSTEM")
    assert envelope.event_id is not None
    assert len(envelope.event_id) > 10
    assert isinstance(envelope.event_timestamp, datetime)
    assert envelope.source == "TEST_SYSTEM"
    assert envelope.schema_version == "1.0.0"
    assert isinstance(envelope.ingestion_timestamp, datetime)


def test_transaction_schema_valid():
    """Verify valid TransactionEvent instantiation and rounding."""
    tx = TransactionEvent(
        source="UPI_GW",
        transaction_id="TXN_1001",
        sender_account_number="SYN10001",
        receiver_account_number="SYN10002",
        amount=Decimal("4999.999"),
        transaction_type="TRANSFER",
        payment_channel="UPI",
    )
    assert tx.amount == Decimal("5000.00")
    assert tx.currency == "INR"
    assert tx.source == "UPI_GW"


def test_transaction_schema_negative_amount_fails():
    """Verify negative or zero amount is rejected."""
    with pytest.raises(ValidationError):
        TransactionEvent(
            source="UPI_GW",
            transaction_id="TXN_1002",
            sender_account_number="SYN10001",
            amount=Decimal("-50.00"),
        )


def test_account_schema_ifsc_validation():
    """Verify valid and invalid Indian IFSC code formats."""
    # Valid IFSC
    acc = AccountEvent(
        source="CBS",
        account_number="SYN998811",
        customer_id="CUST_01",
        bank_name="State Bank of Synth",
        ifsc_code="SYNB0001091",
    )
    assert acc.ifsc_code == "SYNB0001091"

    # Invalid IFSC (only 5 characters)
    with pytest.raises(ValidationError) as exc:
        AccountEvent(
            source="CBS",
            account_number="SYN998811",
            customer_id="CUST_01",
            bank_name="State Bank of Synth",
            ifsc_code="INVALID",
        )
    assert "Invalid Indian IFSC Code format" in str(exc.value)


def test_complaint_schema_valid():
    """Verify valid ComplaintEvent creation."""
    comp = ComplaintEvent(
        source="NCRP_1930",
        complaint_id="CMP_001",
        acknowledgement_no="NCRP-SYN-2024-100001",
        incident_date=datetime.now(timezone.utc),
        reported_date=datetime.now(timezone.utc),
        category="digital arrest scam",
        reported_loss_amount=Decimal("250000.00"),
    )
    assert comp.category == "digital arrest scam"
    assert comp.reported_loss_amount == Decimal("250000.00")


def test_atm_schema_valid():
    """Verify ATMEvent creation."""
    atm = ATMEvent(
        source="ATM_SWITCH",
        atm_interaction_id="ATM_001",
        account_number="SYN10001",
        atm_id="ATM_SYN_4921",
        location_id="LOC_001",
        amount=Decimal("10000.00"),
        status="SUCCESS",
        rapid_cashout_flag=True,
    )
    assert atm.status == "SUCCESS"
    assert atm.rapid_cashout_flag is True


def test_bank_schema_valid():
    """Verify BankEvent metadata validation."""
    bank = BankEvent(
        source="RBI_DIR",
        bank_code="SYNB",
        bank_name="State Bank of Synth",
        category="Public Sector",
        nodal_officer_email="nodal.officer@synthbank.com",
    )
    assert bank.bank_code == "SYNB"
    assert bank.nodal_officer_email == "nodal.officer@synthbank.com"


def test_alert_schema_valid():
    """Verify AlertEvent score boundary enforcement."""
    alert = AlertEvent(
        source="FRAUD_DETECTOR",
        alert_id="ALT_001",
        alert_type="RAPID_VELOCITY",
        severity="CRITICAL",
        triggered_entity_type="ACCOUNT",
        triggered_entity_id="SYN10001",
        description="Mule account drained within 90 seconds",
        risk_score=0.925,
        recommended_action="EMERGENCY_FREEZE",
    )
    assert alert.severity == "CRITICAL"
    assert alert.risk_score == 0.925
