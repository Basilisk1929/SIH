"""Data ingestion and real-time streaming pipeline module."""

from ingestion.connectors.complaint_consumer import ComplaintBatchIngestor
from ingestion.pipelines.synthetic_stream import simulate_transaction_stream

__all__ = ["ComplaintBatchIngestor", "simulate_transaction_stream"]
