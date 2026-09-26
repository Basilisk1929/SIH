"""Aura-compatible, parameterized Cypher queries for cyber intelligence and risk detection.

Every query is crafted to run efficiently in Neo4j Aura (using parameterization, index lookups,
and UNWIND/APOC compatibility) while returning explainable graph evidence.
"""

# ==============================================================================
# 1. FIND ACCOUNTS CONNECTED TO AN ACCOUNT
# ==============================================================================
FIND_CONNECTED_ACCOUNTS = """
MATCH (source:Account {account_number: $account_number})
// 1. Direct Outward Transfers
OPTIONAL MATCH (source)-[r_out:TRANSFERRED_TO]->(acc_out:Account)
WHERE acc_out IS NOT NULL
WITH source, acc_out, 'TRANSFER_OUT' AS conn_type, 1 AS hops, NULL AS shared_id,
     r_out.amount AS amount, r_out.txn_id AS txn_id, acc_out.is_mule AS is_mule, acc_out.mule_tier AS mule_tier
// 2. Direct Inward Transfers
UNION ALL
MATCH (source:Account {account_number: $account_number})
OPTIONAL MATCH (acc_in:Account)-[r_in:TRANSFERRED_TO]->(source)
WHERE acc_in IS NOT NULL
WITH source, acc_in AS acc_out, 'TRANSFER_IN' AS conn_type, 1 AS hops, NULL AS shared_id,
     r_in.amount AS amount, r_in.txn_id AS txn_id, acc_in.is_mule AS is_mule, acc_in.mule_tier AS mule_tier
// 3. Shared Hardware Device (Collusion Link)
UNION ALL
MATCH (source:Account {account_number: $account_number})-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(acc_dev:Account)
WHERE acc_dev.account_number <> source.account_number
WITH source, acc_dev AS acc_out, 'SHARED_DEVICE' AS conn_type, 2 AS hops, d.device_id AS shared_id,
     0.0 AS amount, NULL AS txn_id, acc_dev.is_mule AS is_mule, acc_dev.mule_tier AS mule_tier
// 4. Shared Contact Phone
UNION ALL
MATCH (source:Account {account_number: $account_number})-[:USES_PHONE]->(p:Phone)<-[:USES_PHONE]-(acc_ph:Account)
WHERE acc_ph.account_number <> source.account_number
WITH source, acc_ph AS acc_out, 'SHARED_PHONE' AS conn_type, 2 AS hops, p.phone_number AS shared_id,
     0.0 AS amount, NULL AS txn_id, acc_ph.is_mule AS is_mule, acc_ph.mule_tier AS mule_tier
// 5. Shared UPI Handle
UNION ALL
MATCH (source:Account {account_number: $account_number})-[:USES_UPI]->(u:UPI)<-[:USES_UPI]-(acc_upi:Account)
WHERE acc_upi.account_number <> source.account_number
WITH source, acc_upi AS acc_out, 'SHARED_UPI' AS conn_type, 2 AS hops, u.vpa AS shared_id,
     0.0 AS amount, NULL AS txn_id, acc_upi.is_mule AS is_mule, acc_upi.mule_tier AS mule_tier

RETURN
    source.account_number AS source_account,
    acc_out.account_number AS connected_account,
    conn_type AS connection_type,
    hops AS hop_distance,
    shared_id AS shared_entity_id,
    sum(amount) AS total_amount_inr,
    count(txn_id) AS transaction_count,
    coalesce(is_mule, false) AS is_mule,
    mule_tier AS mule_tier,
    CASE conn_type
        WHEN 'TRANSFER_OUT' THEN 'Direct fund transfer from ' + source.account_number + ' to recipient ' + acc_out.account_number + ' across ' + toString(count(txn_id)) + ' transactions'
        WHEN 'TRANSFER_IN' THEN 'Direct fund receipt by ' + source.account_number + ' from sender ' + acc_out.account_number + ' across ' + toString(count(txn_id)) + ' transactions'
        WHEN 'SHARED_DEVICE' THEN 'Shared hardware device ' + shared_id + ' utilized concurrently by both accounts, indicating shared operator syndicate'
        WHEN 'SHARED_PHONE' THEN 'Shared contact telephone number ' + shared_id + ' linked to KYC profiles of both accounts'
        WHEN 'SHARED_UPI' THEN 'Shared UPI VPA handle ' + shared_id + ' mapped to both bank accounts'
        ELSE 'Graph association detected'
    END AS explanation
ORDER BY is_mule DESC, total_amount_inr DESC, hops ASC
LIMIT $limit
"""

# ==============================================================================
# 2. FIND TRANSACTION CHAINS (Multi-hop Layering Trails)
# ==============================================================================
FIND_TRANSACTION_CHAINS = """
MATCH path = (origin:Account {account_number: $account_number})-[:TRANSFERRED_TO*2..5]->(destination:Account)
WHERE ALL(r IN relationships(path) WHERE r.amount >= $min_amount)
WITH path, origin, destination,
     [n IN nodes(path) | n.account_number] AS node_sequence,
     relationships(path) AS rels,
     length(path) AS hops

WITH path, origin, destination, node_sequence, hops, rels,
     head(rels).timestamp AS start_time,
     last(rels).timestamp AS end_time,
     reduce(s = 0.0, r IN rels | s + r.amount) AS total_flow,
     head([r IN rels | r.amount]) AS initial_amount,
     reduce(min_val = 1000000000.0, r IN rels | CASE WHEN r.amount < min_val THEN r.amount ELSE min_val END) AS min_hop

RETURN
    origin.account_number AS origin_account,
    destination.account_number AS destination_account,
    node_sequence AS path_nodes,
    hops AS hop_count,
    total_flow AS total_flow_amount_inr,
    min_hop AS min_hop_amount_inr,
    start_time AS start_timestamp,
    end_time AS end_timestamp,
    duration.between(datetime(start_time), datetime(end_time)).seconds AS chain_duration_seconds,
    CASE
        WHEN duration.between(datetime(start_time), datetime(end_time)).seconds <= 1800 THEN 'RAPID_PASSTHROUGH'
        WHEN duration.between(datetime(start_time), datetime(end_time)).seconds <= 14400 THEN 'MEDIUM_VELOCITY'
        ELSE 'NORMAL_TIMING'
    END AS velocity_classification,
    'Multi-hop money trail: Funds originating from ' + origin.account_number + ' layered across ' + toString(hops) + ' accounts ending at ' + destination.account_number + ' within ' + toString(duration.between(datetime(start_time), datetime(end_time)).seconds / 60) + ' minutes. Minimum hop bottleneck: ₹' + toString(min_hop) AS explanation
ORDER BY hops DESC, total_flow DESC
LIMIT $limit
"""

# ==============================================================================
# 3. FIND HIGH-DEGREE ACCOUNTS (Funnel Nodes & Dispersal Hubs)
# ==============================================================================
FIND_HIGH_DEGREE_ACCOUNTS = """
MATCH (a:Account)
OPTIONAL MATCH (sender:Account)-[r_in:TRANSFERRED_TO]->(a)
OPTIONAL MATCH (a)-[r_out:TRANSFERRED_TO]->(receiver:Account)

WITH a,
     count(DISTINCT r_in) AS in_degree,
     count(DISTINCT r_out) AS out_degree,
     count(DISTINCT r_in) + count(DISTINCT r_out) AS total_degree,
     count(DISTINCT sender) AS unique_senders,
     count(DISTINCT receiver) AS unique_receivers,
     coalesce(sum(r_in.amount), 0.0) AS credit_vol,
     coalesce(sum(r_out.amount), 0.0) AS debit_vol
WHERE total_degree >= $min_degree

WITH a, in_degree, out_degree, total_degree, unique_senders, unique_receivers, credit_vol, debit_vol,
     CASE
         WHEN in_degree >= 4 AND out_degree <= 2 THEN 'FUNNEL_COLLECTOR'
         WHEN in_degree <= 2 AND out_degree >= 4 THEN 'DISPERSION_HUB'
         WHEN in_degree >= 3 AND out_degree >= 3 THEN 'HIGH_VELOCITY_PASSTHROUGH'
         ELSE 'HIGH_VOLUME'
     END AS typology

RETURN
    a.account_number AS account_number,
    coalesce(a.bank_name, 'Unknown Bank') AS bank_name,
    in_degree,
    out_degree,
    total_degree,
    unique_senders,
    unique_receivers,
    typology AS hub_typology,
    credit_vol AS total_credit_volume,
    debit_vol AS total_debit_volume,
    coalesce(a.is_mule, false) AS is_mule,
    CASE typology
        WHEN 'FUNNEL_COLLECTOR' THEN 'Funnel mule collector: Received deposits from ' + toString(unique_senders) + ' distinct senders totaling ₹' + toString(credit_vol) + ' with minimal outward routing'
        WHEN 'DISPERSION_HUB' THEN 'Dispersion mule hub: Liquidated / disbursed funds to ' + toString(unique_receivers) + ' distinct destinations totaling ₹' + toString(debit_vol)
        WHEN 'HIGH_VELOCITY_PASSTHROUGH' THEN 'High-velocity pass-through conduit: Active two-way transit node bridging ' + toString(unique_senders) + ' senders to ' + toString(unique_receivers) + ' receivers'
        ELSE 'Elevated connectivity node with degree ' + toString(total_degree)
    END AS explanation
ORDER BY total_degree DESC, credit_vol DESC
LIMIT $limit
"""

# ==============================================================================
# 4. FIND SUSPICIOUS ACCOUNT CLUSTERS (Shared Infrastructure & Collusion)
# ==============================================================================
FIND_SUSPICIOUS_CLUSTERS = """
// Cluster Type 1: Shared Device Rings
MATCH (a1:Account)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(a2:Account)
WHERE a1.account_number < a2.account_number
WITH d.device_id AS shared_id, 'SHARED_DEVICE_RING' AS c_type,
     collect(DISTINCT a1.account_number) + collect(DISTINCT a2.account_number) AS members,
     sum(coalesce(a1.current_balance, 0.0) + coalesce(a2.current_balance, 0.0)) AS cluster_vol
WITH shared_id, c_type, [x IN members | x] AS unique_members, cluster_vol
WHERE size(unique_members) >= 2

RETURN
    shared_id AS cluster_id,
    c_type AS cluster_type,
    unique_members AS member_accounts,
    size(unique_members) AS member_count,
    shared_id AS shared_identifier,
    cluster_vol AS total_cluster_volume_inr,
    0.88 AS risk_score,
    'Collusion Ring: ' + toString(size(unique_members)) + ' bank accounts operating simultaneously from hardware device ' + shared_id + ', representing mule operation infrastructure' AS explanation
ORDER BY member_count DESC, total_cluster_volume_inr DESC
LIMIT $limit
"""

# ==============================================================================
# 5. FIND CASH-OUT PATHS (ATM Withdrawals Post-Transfer)
# ==============================================================================
FIND_CASHOUT_PATHS = """
MATCH path = (origin:Account {account_number: $account_number})-[:TRANSFERRED_TO*0..4]->(cashout_acc:Account)-[w:WITHDREW_AT]->(atm:ATM)
OPTIONAL MATCH (atm)-[:LOCATED_AT]->(loc:Location)
WITH origin, cashout_acc, atm, loc, w, path,
     [n IN nodes(path) WHERE n:Account AND n <> origin AND n <> cashout_acc | n.account_number] AS intermediate_nodes,
     length(path) AS path_len

RETURN
    origin.account_number AS origin_account,
    cashout_acc.account_number AS cashout_account,
    atm.atm_id AS atm_id,
    coalesce(atm.location_name, 'ATM Terminal') + ', ' + coalesce(loc.city, 'Unknown City') + ', ' + coalesce(loc.state, 'Unknown State') AS atm_location,
    w.amount AS withdrawn_amount_inr,
    toString(w.timestamp) AS withdrawal_timestamp,
    intermediate_nodes AS intermediary_mules,
    coalesce(w.rapid_cashout, false) AS rapid_cashout,
    'Fund Liquidation Trail: Origin account ' + origin.account_number + ' funds reached terminal mule ' + cashout_acc.account_number + ' via ' + toString(path_len) + ' hops and were withdrawn as ₹' + toString(w.amount) + ' cash at ' + atm.atm_id + ' located in ' + coalesce(loc.city, 'N/A') AS explanation
ORDER BY w.amount DESC
LIMIT $limit
"""

# ==============================================================================
# 6. FIND ACCOUNTS CONNECTED TO COMPLAINTS
# ==============================================================================
FIND_ACCOUNTS_CONNECTED_TO_COMPLAINTS = """
// Match complaints and linked suspect accounts (0-hop direct mention, or 1-2 hop beneficiaries)
MATCH (cmp:Complaint)
WHERE ($category IS NULL OR cmp.category = $category)
  AND ($min_loss IS NULL OR cmp.reported_loss_amount >= $min_loss)

// Direct suspect mentioned in complaint
OPTIONAL MATCH (cmp)<-[:MENTIONED_IN]-(suspect:Account)
OPTIONAL MATCH (suspect)-[:TRANSFERRED_TO]->(layer1:Account)
OPTIONAL MATCH (layer1)-[:TRANSFERRED_TO]->(layer2:Account)

WITH cmp, suspect, layer1, layer2,
     CASE
         WHEN layer2 IS NOT NULL THEN layer2
         WHEN layer1 IS NOT NULL THEN layer1
         ELSE suspect
     END AS connected_acc,
     CASE
         WHEN layer2 IS NOT NULL THEN 2
         WHEN layer1 IS NOT NULL THEN 1
         ELSE 0
     END AS depth,
     CASE
         WHEN layer2 IS NOT NULL THEN 'LAYER_2_BENEFICIARY'
         WHEN layer1 IS NOT NULL THEN 'LAYER_1_RECIPIENT'
         ELSE 'DIRECT_REPORTED_SUSPECT'
     END AS route
WHERE connected_acc IS NOT NULL

RETURN DISTINCT
    cmp.acknowledgement_no AS acknowledgement_no,
    cmp.category AS category,
    cmp.reported_loss_amount AS reported_loss_inr,
    connected_acc.account_number AS connected_account,
    depth AS connection_depth,
    route AS connection_route,
    toString(cmp.reported_date) AS complaint_reported_date,
    cmp.suspect_upi_id AS suspect_upi,
    cmp.suspect_phone_number AS suspect_phone,
    'NCRP Complaint Link: Citizen reported ₹' + toString(cmp.reported_loss_amount) + ' loss under category [' + cmp.category + ']. Account ' + connected_acc.account_number + ' is linked at Depth ' + toString(depth) + ' via route ' + route AS explanation
ORDER BY cmp.reported_loss_amount DESC, depth ASC
LIMIT $limit
"""

# ==============================================================================
# 7. FIND SHORTEST SUSPICIOUS PATHS
# ==============================================================================
FIND_SHORTEST_SUSPICIOUS_PATHS = """
MATCH (src:Account {account_number: $source_account}),
      (dst:Account {account_number: $target_account})
MATCH path = shortestPath((src)-[:TRANSFERRED_TO*..8]->(dst))
WITH path, src, dst,
     nodes(path) AS n_list,
     relationships(path) AS r_list,
     length(path) AS hops

RETURN
    src.account_number AS source_entity,
    dst.account_number AS target_entity,
    hops AS hop_count,
    [n IN n_list | {account_number: n.account_number, is_mule: coalesce(n.is_mule, false), mule_tier: n.mule_tier}] AS path_nodes,
    [r IN r_list | {txn_id: r.txn_id, amount: r.amount, timestamp: toString(r.timestamp), rail_type: r.rail_type, is_suspicious: coalesce(r.is_suspicious, false)}] AS path_relationships,
    reduce(s = 0.0, r IN r_list | s + r.amount) AS total_amount_inr,
    ANY(n IN n_list WHERE coalesce(n.is_mule, false) = true) OR ANY(r IN r_list WHERE coalesce(r.is_suspicious, false) = true) AS is_suspicious_path,
    'Shortest Money Laundering Path: ' + toString(hops) + ' transfer hops connecting ' + src.account_number + ' to ' + dst.account_number + ' transferring ₹' + toString(reduce(s = 0.0, r IN r_list | s + r.amount)) + ' across financial rails' AS explanation
"""
