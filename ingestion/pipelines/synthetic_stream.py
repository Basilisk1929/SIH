"""Simulated high-throughput financial transaction stream for stress-testing and demo."""

import asyncio
from datetime import datetime, timezone
import random
from typing import AsyncGenerator, Dict, Any


async def simulate_transaction_stream(
    tps: float = 2.0, total_events: int = 50
) -> AsyncGenerator[Dict[str, Any], None]:
    """Async generator emitting synthetic transaction events at specified TPS."""
    delay = 1.0 / tps
    for i in range(total_events):
        amount = float(random.randint(1, 100) * 1000)
        is_suspicious = amount > 50000 or random.random() < 0.15
        event = {
            "event_id": f"evt-{i+1}",
            "txn_ref_no": f"UPI/4289{random.randint(10000, 99999)}/SYN",
            "sender_upi": f"citizen_{random.randint(1, 100)}@synthbank",
            "receiver_upi": f"mule_{random.randint(1, 20)}@synthaxis",
            "amount_inr": amount,
            "rail_type": random.choice(["UPI", "IMPS"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_flagged_suspicious": is_suspicious,
        }
        yield event
        await asyncio.sleep(delay)
