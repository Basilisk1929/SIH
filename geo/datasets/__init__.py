"""Geospatial datasets package."""

from geo.datasets.rbi_atm_registry import RBIAtmRegistry, BankOutlet
from geo.datasets.validation.chicago_benchmark import ChicagoCrimeValidationBenchmark

__all__ = ["RBIAtmRegistry", "BankOutlet", "ChicagoCrimeValidationBenchmark"]
