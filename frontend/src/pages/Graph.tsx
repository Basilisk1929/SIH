import React, { useEffect, useState, useRef, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { GraphService } from '../services/graph';
import { SubgraphData, GraphNode, GraphEdge } from '../types';

interface LayoutNode extends GraphNode {
  x: number;
  y: number;
  vx?: number;
  vy?: number;
}

export const Graph: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const initialAccount = searchParams.get('account') || 'SYN1122334455';
  const [centerAccount, setCenterAccount] = useState(initialAccount);
  const [depth, setDepth] = useState<number>(2);

  const [graphData, setGraphData] = useState<SubgraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected node for inspection
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Filters
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchFilter, setSearchFilter] = useState('');

  // Zoom & Pan state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Cashout paths overlay
  const [cashoutPaths, setCashoutPaths] = useState<any[] | null>(null);
  const [pathLoading, setPathLoading] = useState(false);

  const svgRef = useRef<SVGSVGElement | null>(null);

  const loadGraph = async (acc: string, d: number) => {
    try {
      setLoading(true);
      setError(null);
      setSelectedNode(null);
      const data = await GraphService.getNetworkGraph(acc, d);
      setGraphData(data);

      // Auto-select center node if present
      if (data?.nodes?.length) {
        const center = data.nodes.find((n) => n.id === acc || (n.properties as any)?.account_number === acc) || data.nodes[0];
        setSelectedNode(center);
      }
    } catch (err: any) {
      console.error('Failed to load Neo4j network graph:', err);
      setError(err.message || 'Unable to retrieve multi-hop graph topology from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph(centerAccount, depth);
  }, [centerAccount, depth]);

  const handleTraceCashout = async () => {
    try {
      setPathLoading(true);
      const res = await GraphService.getCashoutPaths(centerAccount, 4);
      setCashoutPaths(res?.paths || []);
    } catch (err: any) {
      console.warn('Cashout path trace note:', err);
    } finally {
      setPathLoading(false);
    }
  };

  // Node coloring
  const getNodeColor = (label: string, isCenter = false) => {
    if (isCenter) return { fill: '#00f2fe', stroke: '#fff', text: '#070a12' };
    switch (label?.toUpperCase()) {
      case 'BANKACCOUNT':
      case 'ACCOUNT':
        return { fill: '#3b82f6', stroke: '#60a5fa', text: '#fff' };
      case 'UPI_ID':
      case 'UPI':
        return { fill: '#6366f1', stroke: '#818cf8', text: '#fff' };
      case 'PHONE':
        return { fill: '#f59e0b', stroke: '#fbbf24', text: '#070a12' };
      case 'DEVICE':
      case 'IMEI':
        return { fill: '#ec4899', stroke: '#f472b6', text: '#fff' };
      case 'COMPLAINT':
        return { fill: '#a855f7', stroke: '#c084fc', text: '#fff' };
      case 'ATM':
      case 'CASHOUT':
        return { fill: '#ef4444', stroke: '#f87171', text: '#fff' };
      case 'MULERING':
        return { fill: '#dc2626', stroke: '#ef4444', text: '#fff' };
      default:
        return { fill: '#64748b', stroke: '#94a3b8', text: '#fff' };
    }
  };

  // Compute Layout coordinates for nodes
  const layoutNodes: LayoutNode[] = useMemo(() => {
    if (!graphData?.nodes || graphData.nodes.length === 0) return [];

    const nodes = graphData.nodes;
    const width = 900;
    const height = 540;
    const centerX = width / 2;
    const centerY = height / 2;

    // Center node in middle
    const centerIdx = nodes.findIndex((n) => n.id === centerAccount || (n.properties as any)?.account_number === centerAccount);
    const result: LayoutNode[] = [];

    // Simple concentric circular layout for predictable forensic clarity
    const outerNodes = nodes.filter((_, idx) => idx !== centerIdx);
    const centerNode = centerIdx >= 0 ? nodes[centerIdx] : nodes[0];

    result.push({
      ...centerNode,
      x: centerX,
      y: centerY,
    });

    const angleStep = (2 * Math.PI) / Math.max(1, outerNodes.length);
    const radius = Math.min(width, height) * 0.38;

    outerNodes.forEach((n, idx) => {
      // Stagger radius slightly based on type or hop for organic feel
      const r = (n.properties as any)?.hop === 2 ? radius * 1.15 : radius;
      const angle = idx * angleStep;
      result.push({
        ...n,
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
      });
    });

    return result;
  }, [graphData, centerAccount]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, LayoutNode>();
    layoutNodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [layoutNodes]);

  // Mouse pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const filteredNodes = layoutNodes.filter((n) => {
    if (filterType !== 'ALL' && n.label?.toUpperCase() !== filterType) return false;
    if (searchFilter.trim() && !n.id.toLowerCase().includes(searchFilter.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            🕸️ Neo4j Multi-Hop Graph Link Analysis
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            Interactive topology revealing money laundering fan-out, layering paths, shared device IMEIs, and ATM cash-out points.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            className="btn-action"
            onClick={handleTraceCashout}
            disabled={pathLoading}
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: pathLoading ? 'not-allowed' : 'pointer',
            }}
          >
            {pathLoading ? 'Tracing Paths...' : '⚡ Trace Cash-Out Dissipation Paths'}
          </button>
        </div>
      </div>

      {/* Control bar */}
      <div
        className="stat-card"
        style={{
          display: 'flex',
          gap: 16,
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: '12px 18px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)' }}>Focus Entity:</label>
          <input
            type="text"
            value={centerAccount}
            onChange={(e) => setCenterAccount(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 12px',
              borderRadius: 6,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              width: 200,
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Depth:</label>
          <select
            value={depth}
            onChange={(e) => setDepth(parseInt(e.target.value))}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 10px',
              borderRadius: 6,
              fontSize: '0.85rem',
            }}
          >
            <option value={1}>1 Hop (Direct)</option>
            <option value={2}>2 Hops (Mule Layer 2)</option>
            <option value={3}>3 Hops (Full Syndicate)</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Entity Filter:</label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 10px',
              borderRadius: 6,
              fontSize: '0.85rem',
            }}
          >
            <option value="ALL">All Entity Types</option>
            <option value="BANKACCOUNT">Bank Account</option>
            <option value="UPI_ID">UPI Identifier</option>
            <option value="PHONE">Phone Number</option>
            <option value="DEVICE">Device / IMEI</option>
            <option value="COMPLAINT">Complaint</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="text"
            placeholder="Filter entities in view..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: '0.85rem',
              width: 170,
            }}
          />
        </div>

        {/* Zoom Controls */}
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginLeft: 'auto' }}>
          <button
            className="btn-action"
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
            style={{ padding: '6px 10px', fontSize: '0.85rem' }}
          >
            🔍+
          </button>
          <button
            className="btn-action"
            onClick={() => setZoom((z) => Math.max(0.4, z - 0.2))}
            style={{ padding: '6px 10px', fontSize: '0.85rem' }}
          >
            🔍-
          </button>
          <button
            className="btn-action"
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            style={{ padding: '6px 10px', fontSize: '0.8rem' }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Main Graph Canvas & Inspection Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 340px' : '1fr', gap: 20 }}>
        {/* SVG Interactive Canvas */}
        <div
          className="stat-card"
          style={{
            position: 'relative',
            minHeight: 560,
            overflow: 'hidden',
            padding: 0,
            background: 'radial-gradient(circle at center, #0f172a 0%, #070a12 100%)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 10,
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          {loading ? (
            <LoadingSpinner text="Traversing Neo4j entity graph..." minHeight={560} />
          ) : error ? (
            <div style={{ padding: 40 }}>
              <ErrorMessage message={error} onRetry={() => loadGraph(centerAccount, depth)} />
            </div>
          ) : (
            <svg
              ref={svgRef}
              width="100%"
              height="560"
              viewBox="0 0 900 540"
              style={{ display: 'block', userSelect: 'none' }}
            >
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="8"
                  markerHeight="6"
                  refX="18"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 8 3, 0 6" fill="#00f2fe" opacity="0.8" />
                </marker>
                <marker
                  id="arrowhead-red"
                  markerWidth="8"
                  markerHeight="6"
                  refX="18"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 8 3, 0 6" fill="#ef4444" opacity="0.9" />
                </marker>
              </defs>

              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                {/* Render Edges */}
                {graphData?.edges?.map((edge: GraphEdge, idx: number) => {
                  const sourceNode = nodeMap.get(edge.source);
                  const targetNode = nodeMap.get(edge.target);
                  if (!sourceNode || !targetNode) return null;

                  const isHighVelocity = (edge.properties as any)?.time_delta_seconds && (edge.properties as any).time_delta_seconds < 300;
                  const strokeColor = isHighVelocity ? '#ef4444' : 'rgba(0, 242, 254, 0.4)';
                  const marker = isHighVelocity ? 'url(#arrowhead-red)' : 'url(#arrowhead)';

                  const midX = (sourceNode.x + targetNode.x) / 2;
                  const midY = (sourceNode.y + targetNode.y) / 2;

                  return (
                    <g key={`edge-${idx}`}>
                      <line
                        x1={sourceNode.x}
                        y1={sourceNode.y}
                        x2={targetNode.x}
                        y2={targetNode.y}
                        stroke={strokeColor}
                        strokeWidth={isHighVelocity ? 2.5 : 1.5}
                        strokeDasharray={edge.relationship === 'LINKED_PHONE' ? '4 3' : undefined}
                        markerEnd={marker}
                      />
                      {/* Edge label */}
                      <text
                        x={midX}
                        y={midY - 4}
                        fill="rgba(255,255,255,0.6)"
                        fontSize="9"
                        fontFamily="var(--font-mono)"
                        textAnchor="middle"
                      >
                        {edge.relationship}
                      </text>
                    </g>
                  );
                })}

                {/* Render Nodes */}
                {filteredNodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  const isCenter = node.id === centerAccount;
                  const color = getNodeColor(node.label, isCenter);

                  return (
                    <g
                      key={`node-${node.id}`}
                      transform={`translate(${node.x}, ${node.y})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNode(node);
                      }}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Outer pulse circle for selected or center */}
                      {(isSelected || isCenter) && (
                        <circle
                          r="26"
                          fill="none"
                          stroke={isCenter ? '#00f2fe' : '#60a5fa'}
                          strokeWidth="2"
                          strokeDasharray="4 2"
                          opacity="0.8"
                        />
                      )}

                      {/* Main node circle */}
                      <circle
                        r="18"
                        fill={color.fill}
                        stroke={color.stroke}
                        strokeWidth={isSelected ? 3 : 1.5}
                      />

                      {/* Node label code */}
                      <text
                        y="4"
                        fill={color.text}
                        fontSize="10"
                        fontWeight="bold"
                        textAnchor="middle"
                      >
                        {node.label?.slice(0, 3).toUpperCase()}
                      </text>

                      {/* Node Identifier under circle */}
                      <text
                        y="30"
                        fill="#fff"
                        fontSize="10"
                        fontFamily="var(--font-mono)"
                        textAnchor="middle"
                        style={{ textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}
                      >
                        {node.id.length > 14 ? `${node.id.slice(0, 12)}...` : node.id}
                      </text>
                    </g>
                  );
                })}
              </g>
            </svg>
          )}

          {/* Legend Overlay */}
          <div
            style={{
              position: 'absolute',
              bottom: 12,
              left: 12,
              background: 'rgba(7, 10, 18, 0.85)',
              backdropFilter: 'blur(4px)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 6,
              padding: '8px 12px',
              display: 'flex',
              gap: 12,
              fontSize: '0.74rem',
              color: 'var(--text-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#00f2fe' }} /> Center Focus
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6' }} /> Bank Account
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#6366f1' }} /> UPI VPA
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }} /> Phone
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ec4899' }} /> Device / IMEI
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} /> ATM / Cash-Out
            </div>
          </div>
        </div>

        {/* Selected Entity Forensic Inspector Panel */}
        {selectedNode && (
          <div className="stat-card" style={{ height: 'fit-content', padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Entity Inspector
              </span>
              <Badge variant="HIGH">{selectedNode.label}</Badge>
            </div>

            <h3 style={{ margin: '0 0 10px 0', fontSize: '1.05rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
              {selectedNode.id}
            </h3>

            {/* Properties breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.82rem', marginBottom: 16 }}>
              {Object.entries(selectedNode.properties || {}).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: 4 }}>
                  <span style={{ color: 'var(--text-muted)' }}>{k}:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </span>
                </div>
              ))}
            </div>

            {/* Quick Actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(selectedNode.label?.toUpperCase() === 'BANKACCOUNT' || selectedNode.label?.toUpperCase() === 'ACCOUNT') && (
                <Link
                  to={`/accounts/${encodeURIComponent(selectedNode.id)}`}
                  className="btn-action"
                  style={{
                    textAlign: 'center',
                    padding: '8px',
                    fontSize: '0.8rem',
                    background: 'var(--accent-cyan)',
                    color: '#070a12',
                    fontWeight: 700,
                    textDecoration: 'none',
                    borderRadius: 6,
                  }}
                >
                  Inspect Account Dossier →
                </Link>
              )}

              <button
                className="btn-action"
                onClick={() => {
                  setCenterAccount(selectedNode.id);
                  setSearchParams({ account: selectedNode.id });
                }}
                style={{
                  padding: '8px',
                  fontSize: '0.8rem',
                  background: 'rgba(255,255,255,0.06)',
                  color: 'var(--text-primary)',
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              >
                🎯 Re-center Graph Around This Node
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Cash-Out Paths Drawer if traced */}
      {cashoutPaths && cashoutPaths.length > 0 && (
        <div className="stat-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--accent-rose)', margin: '0 0 12px 0' }}>
            ⚡ Detected Rapid Cash-Out Dissipation Paths
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {cashoutPaths.map((p, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-primary)',
                  padding: '12px 16px',
                  borderRadius: 8,
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  flexWrap: 'wrap',
                }}
              >
                <span style={{ fontWeight: 700, color: 'var(--accent-rose)', fontSize: '0.85rem' }}>
                  Path #{idx + 1}:
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                  {(p.path_nodes || []).join('  —[Hop]→  ')}
                </span>
                <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Total Hops: {p.total_hops || 2}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
