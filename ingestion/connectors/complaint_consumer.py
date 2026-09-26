"""Batch complaint ingestion connector for synthetic NCRP/1930 records."""

import json
from pathlib import Path
from typing import Any, Dict, List


class ComplaintBatchIngestor:
    """Reads, validates, and normalizes synthetic complaint feed files."""

    @staticmethod
    def load_from_file(file_path: str | Path) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Complaint feed file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)

        valid_records = []
        for r in records:
            # Minimal schema validation check
            if "acknowledgement_no" in r and "category" in r and "reported_loss_inr" in r:
                valid_records.append(r)

        return valid_records
