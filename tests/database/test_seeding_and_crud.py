"""Integration tests for database seeding and relational CRUD queries."""

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.seeds import seed_database
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


@pytest_asyncio.fixture
async def test_db_session():
    """Async session fixture bound to in-memory SQLite database with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_database_populates_all_ten_tables(test_db_session: AsyncSession):
    """Verify seed_database populates every table with interconnected synthetic records."""
    counts = await seed_database(test_db_session)

    # Verify counts returned by seeder
    assert counts["roles"] >= 5
    assert counts["users"] >= 5
    assert counts["banks"] >= 10
    assert counts["atms"] >= 10
    assert counts["accounts"] >= 40
    assert counts["transactions"] >= 50
    assert counts["cases"] >= 3
    assert counts["complaints"] >= 15
    assert counts["alerts"] >= 10

    # Query counts from database directly
    roles_count = await test_db_session.scalar(select(func.count(Role.id)))
    users_count = await test_db_session.scalar(select(func.count(User.id)))
    banks_count = await test_db_session.scalar(select(func.count(Bank.id)))
    accounts_count = await test_db_session.scalar(select(func.count(Account.id)))
    txns_count = await test_db_session.scalar(select(func.count(Transaction.id)))
    cases_count = await test_db_session.scalar(select(func.count(Case.id)))
    complaints_count = await test_db_session.scalar(select(func.count(Complaint.id)))
    alerts_count = await test_db_session.scalar(select(func.count(Alert.id)))
    audit_count = await test_db_session.scalar(select(func.count(AuditLog.id)))

    assert roles_count >= 5
    assert users_count >= 5
    assert banks_count >= 10
    assert accounts_count >= 40
    assert txns_count >= 50
    assert cases_count >= 3
    assert complaints_count >= 15
    assert alerts_count >= 10
    assert audit_count >= 3


@pytest.mark.asyncio
async def test_relational_queries_and_foreign_keys(test_db_session: AsyncSession):
    """Verify join and relationship traversal across accounts, transactions, and complaints."""
    await seed_database(test_db_session)

    # 1. Verify User -> Role relationship
    stmt_user = select(User).where(User.email == "investigator@cybercell.gov.in")
    investigator = await test_db_session.scalar(stmt_user)
    assert investigator is not None
    assert investigator.role_rel is not None
    assert investigator.role_rel.name == "investigator"
    assert investigator.role == "investigator"

    # 2. Verify Account -> Bank relationship
    stmt_acc = select(Account).where(Account.bank_id.isnot(None)).limit(1)
    account = await test_db_session.scalar(stmt_acc)
    assert account is not None
    assert account.bank is not None
    assert len(account.bank.bank_code) > 0

    # 3. Verify Complaint -> Case relationship
    stmt_comp = select(Complaint).where(Complaint.case_id.isnot(None)).limit(1)
    linked_complaint = await test_db_session.scalar(stmt_comp)
    assert linked_complaint is not None
    assert linked_complaint.case is not None
    assert linked_complaint.case.case_number.startswith("CASE-")

    # 4. Verify Case -> Complaints collection
    stmt_case = select(Case).where(Case.case_number == "CASE-2024-00101")
    first_case = await test_db_session.scalar(stmt_case)
    assert first_case is not None
    assert first_case.assigned_to is not None
    assert first_case.assigned_to.email == "investigator@cybercell.gov.in"

    # 5. Verify Alert -> Account and Transaction linkage
    stmt_alert = select(Alert).where(Alert.account_id.isnot(None)).limit(1)
    alert = await test_db_session.scalar(stmt_alert)
    assert alert is not None
    assert alert.account is not None
    assert alert.account.account_number.startswith("SYN")


@pytest.mark.asyncio
async def test_soft_deletion_query_filtering(test_db_session: AsyncSession):
    """Verify soft deletion flags and query exclusion."""
    await seed_database(test_db_session)

    # Pick an active bank
    bank = await test_db_session.scalar(select(Bank).where(Bank.is_deleted == False).limit(1))
    assert bank is not None
    bank_id = bank.id

    # Soft delete the bank
    bank.soft_delete()
    await test_db_session.commit()

    # Query without soft-deleted filter should not find it
    active_bank = await test_db_session.scalar(
        select(Bank).where(Bank.id == bank_id, Bank.is_deleted == False)
    )
    assert active_bank is None

    # Query with is_deleted == True should find it
    deleted_bank = await test_db_session.scalar(
        select(Bank).where(Bank.id == bank_id, Bank.is_deleted == True)
    )
    assert deleted_bank is not None
    assert deleted_bank.deleted_at is not None

    # Restore
    deleted_bank.restore()
    await test_db_session.commit()

    restored_bank = await test_db_session.scalar(
        select(Bank).where(Bank.id == bank_id, Bank.is_deleted == False)
    )
    assert restored_bank is not None
    assert restored_bank.is_deleted is False
