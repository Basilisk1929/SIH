"""CSV ingestion service parsing streaming or batch CSV records into normalized entities."""

import csv
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from ingestion.app.services.json_ingestor import JSONIngestionService

logger = logging.getLogger(__name__)


class CSVIngestionService:
    """Parses, normalizes, and ingests batch CSV tabular files and stream buffers."""

    @classmethod
    async def ingest_csv_content(
        cls,
        entity_type: str,
        csv_text: str,
        source: str = "CSV_UPLOAD",
    ) -> Dict[str, Any]:
        """Parse raw CSV text into dictionary records and process through validation pipeline."""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        records: List[Dict[str, Any]] = []

        for row in reader:
            # Clean string whitespace and empty string conversions
            clean_row = {}
            for k, v in row.items():
                if k is None:
                    continue
                clean_key = k.strip()
                clean_val = v.strip() if isinstance(v, str) else v
                clean_row[clean_key] = clean_val
            records.append(clean_row)

        if not records:
            return {
                "total_records": 0,
                "accepted_count": 0,
                "rejected_count": 0,
                "duplicate_count": 0,
                "message": "Empty CSV or no data rows detected.",
            }

        return await JSONIngestionService.ingest_batch(
            entity_type=entity_type,
            records=records,
            source=source,
        )

    @classmethod
    async def ingest_csv_file(
        cls,
        entity_type: str,
        file_path: str | Path,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest a CSV file directly from filesystem."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        src_name = source or f"FILE:{path.name}"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return await cls.ingest_csv_content(
            entity_type=entity_type,
            csv_text=content,
            source=src_name,
        )
