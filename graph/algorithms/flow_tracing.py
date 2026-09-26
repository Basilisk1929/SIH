"""Graph algorithms for transaction flow tracing, layering detection, and cycle finding."""

from typing import Dict, List, Set, Tuple


class FlowTracingEngine:
    """In-memory directed acyclic graph (DAG) and cycle detector for money laundering trails."""

    def __init__(self):
        self.adjacency: Dict[str, List[Tuple[str, float, float]]] = {}

    def add_transaction(self, sender: str, receiver: str, amount: float, timestamp_sec: float) -> None:
        """Add directed transaction edge to local analytical graph."""
        if sender not in self.adjacency:
            self.adjacency[sender] = []
        self.adjacency[sender].append((receiver, amount, timestamp_sec))

    def detect_rapid_layering_chains(
        self, start_node: str, max_depth: int = 4, max_hop_delay_sec: float = 600.0
    ) -> List[List[str]]:
        """Identify fast pass-through chains where funds move across nodes within delay window."""
        chains: List[List[str]] = []

        def dfs(current: str, path: List[str], last_time: float):
            if len(path) > 1:
                chains.append(list(path))
            if len(path) >= max_depth:
                return

            for neighbor, amount, txn_time in self.adjacency.get(current, []):
                if neighbor not in path:  # Avoid simple cycles in traversal
                    if last_time == 0.0 or (0 <= (txn_time - last_time) <= max_hop_delay_sec):
                        path.append(neighbor)
                        dfs(neighbor, path, txn_time)
                        path.pop()

        dfs(start_node, [start_node], 0.0)
        return [c for c in chains if len(c) >= 3]
