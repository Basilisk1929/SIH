"""Tests for Neo4j Aura schema constraints and property index statements."""

import pytest
from unittest.mock import AsyncMock
from graph.schema.constraints import CONSTRAINTS, INDEXES, apply_graph_schema


def test_constraints_syntax_aura_compatible():
    """Verify all constraints use Neo4j 5.x / Aura CREATE CONSTRAINT ... REQUIRE ... IS UNIQUE syntax."""
    assert len(CONSTRAINTS) >= 10
    required_labels = ["Customer", "Account", "Transaction", "Complaint", "UPI", "Phone", "Device", "Bank", "ATM", "Location"]

    for label in required_labels:
        matching = [c for c in CONSTRAINTS if f":{label})" in c]
        assert len(matching) >= 1, f"Missing unique constraint for {label}"
        constraint_str = matching[0]
        assert "CREATE CONSTRAINT" in constraint_str
        assert "IF NOT EXISTS" in constraint_str
        assert "REQUIRE" in constraint_str
        assert "IS UNIQUE" in constraint_str


def test_indexes_syntax_aura_compatible():
    """Verify all property indexes use modern Aura CREATE INDEX ... ON syntax."""
    assert len(INDEXES) >= 10
    for idx in INDEXES:
        assert "CREATE INDEX" in idx
        assert "IF NOT EXISTS" in idx
        assert "FOR" in idx
        assert "ON" in idx


@pytest.mark.asyncio
async def test_apply_graph_schema_executes_all_statements():
    """Verify apply_graph_schema executes all constraints and indexes against a session."""
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()

    total_statements = len(CONSTRAINTS) + len(INDEXES)
    executed = await apply_graph_schema(mock_session)

    assert executed == total_statements
    assert mock_session.run.call_count == total_statements
