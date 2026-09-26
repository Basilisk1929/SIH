"""Automated unit test for synthetic data integrity and schema validation."""

import pytest
from data.validators.validate_referential_integrity import DataIntegrityValidator


def test_synthetic_csv_referential_integrity():
    """Verify that generated CSV datasets satisfy 100% referential integrity constraints."""
    validator = DataIntegrityValidator(data_format="csv")
    success = validator.run_all_validations()
    assert success is True, f"Integrity validation failed with errors: {validator.errors}"


def test_synthetic_parquet_referential_integrity():
    """Verify that generated Parquet datasets satisfy 100% referential integrity constraints."""
    validator = DataIntegrityValidator(data_format="parquet")
    success = validator.run_all_validations()
    assert success is True, f"Integrity validation failed with errors: {validator.errors}"
