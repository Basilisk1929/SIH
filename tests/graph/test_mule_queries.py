"""Tests for graph flow tracing engine and mule chain traversal algorithms."""

from graph.algorithms.flow_tracing import FlowTracingEngine


def test_flow_tracing_detects_rapid_layering():
    """Verify directed graph DFS identifies rapid multi-hop pass-through chains."""
    engine = FlowTracingEngine()

    # Chain: Victim -> Mule 1 (t=100) -> Mule 2 (t=220) -> Cashout (t=380)
    engine.add_transaction("VIC_01", "MULE_L1", 50000.0, 100.0)
    engine.add_transaction("MULE_L1", "MULE_L2", 48000.0, 220.0)
    engine.add_transaction("MULE_L2", "CASHOUT_ATM", 46000.0, 380.0)

    # Isolated unrelated transfer
    engine.add_transaction("CLEAN_ACC_A", "CLEAN_ACC_B", 500.0, 5000.0)

    chains = engine.detect_rapid_layering_chains("VIC_01", max_depth=4, max_hop_delay_sec=300.0)
    assert len(chains) >= 1
    longest_chain = max(chains, key=len)
    assert longest_chain == ["VIC_01", "MULE_L1", "MULE_L2", "CASHOUT_ATM"]
