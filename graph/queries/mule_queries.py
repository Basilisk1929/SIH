"""Curated, parameterized Neo4j Cypher query templates for cyber intelligence investigations."""

# 1. Expand immediate neighborhood of a suspect entity
EXPAND_SUSPECT_NEIGHBORHOOD = """
MATCH (suspect:BankAccount {account_number: $account_number})
OPTIONAL MATCH (suspect)-[r1:TRANSFERRED_TO]->(mule:BankAccount)
OPTIONAL MATCH (suspect)-[r2:LINKED_PHONE]->(phone:Phone)
OPTIONAL MATCH (suspect)-[r3:ACCESSED_FROM]->(device:Device)
RETURN suspect, collect(DISTINCT mule) as mules, collect(DISTINCT phone) as phones, collect(DISTINCT device) as devices
"""

# 2. Multi-hop money flow laundering chain (Up to 4 layers)
TRACE_MULTI_HOP_FLOW = """
MATCH path = (origin:BankAccount {account_number: $origin_account})-[:TRANSFERRED_TO*1..4]->(destination:BankAccount)
WHERE ALL(r IN relationships(path) WHERE r.amount >= $min_amount)
RETURN path
ORDER BY length(path) DESC
LIMIT 20
"""

# 3. Detect shared device / IMEI / IP links across supposedly distinct accounts
FIND_COLLUSION_CLUSTERS = """
MATCH (a1:BankAccount)-[:ACCESSED_FROM]->(d:Device)<-[:ACCESSED_FROM]-(a2:BankAccount)
WHERE a1.account_number < a2.account_number
RETURN d.device_id as shared_device, collect(DISTINCT a1.account_number) + collect(DISTINCT a2.account_number) as collusion_ring
LIMIT 50
"""

# 4. Shortest path between a victim complaint and a known mule syndicate cash-out node
SHORTEST_PATH_TO_CASHOUT = """
MATCH (source:BankAccount {account_number: $source_account}),
      (cashout:BankAccount {layer: 'Layer-3 Cash-out'})
MATCH path = shortestPath((source)-[:TRANSFERRED_TO*..6]->(cashout))
RETURN path
"""
