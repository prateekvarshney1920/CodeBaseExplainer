"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";

/** Language → node styling for light mode */
const LANG_STYLES = {
  python: { bg: "#3776AB", text: "#fff", mini: "#3776AB" },
  javascript: { bg: "#F0DB4F", text: "#1a1a2e", mini: "#F0DB4F" },
  typescript: { bg: "#3178C6", text: "#fff", mini: "#3178C6" },
  java: { bg: "#ED8B00", text: "#fff", mini: "#ED8B00" },
  go: { bg: "#00ADD8", text: "#fff", mini: "#00ADD8" },
  cpp: { bg: "#00599C", text: "#fff", mini: "#00599C" },
  c: { bg: "#5F6B7C", text: "#fff", mini: "#5F6B7C" },
  csharp: { bg: "#239120", text: "#fff", mini: "#239120" },
  ruby: { bg: "#CC342D", text: "#fff", mini: "#CC342D" },
  rust: { bg: "#DEA584", text: "#1a1a2e", mini: "#DEA584" },
  unknown: { bg: "#6B7280", text: "#fff", mini: "#6B7280" },
};

/** Node dimensions for dagre layout */
const NODE_WIDTH = 200;
const NODE_HEIGHT = 64;

/**
 * Compute a dagre-based tree layout (top → bottom).
 */
function getLayoutedElements(nodes, edges) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: "TB",       // Top-to-Bottom tree
    nodesep: 60,         // Horizontal spacing between siblings
    ranksep: 100,        // Vertical spacing between ranks
    marginx: 40,
    marginy: 40,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

/**
 * DependencyGraph — Interactive tree-structured graph using React Flow + dagre.
 */
export default function DependencyGraph({
  graphData,
  onNodeClick,
  selectedNode,
  entryPoints = [],
  cycles = [],
}) {
  const cycleFiles = useMemo(() => new Set((cycles || []).flat()), [cycles]);
  const entrySet = useMemo(() => new Set(entryPoints || []), [entryPoints]);

  // Prepare nodes with light-mode styling
  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    if (!graphData?.nodes) return { layoutedNodes: [], layoutedEdges: [] };

    const rawNodes = graphData.nodes.map((node) => {
      const lang = node.data?.language || "unknown";
      const style = LANG_STYLES[lang] || LANG_STYLES.unknown;
      const isEntry = entrySet.has(node.id);
      const inCycle = cycleFiles.has(node.id);
      const isSelected = selectedNode === node.id;

      return {
        ...node,
        data: {
          ...node.data,
          label: (
            <div className="graph-node-label">
              <span className="graph-node-name">
                {isEntry ? "⚡ " : ""}
                {inCycle ? "⚠️ " : ""}
                {node.data?.label || node.id}
              </span>
              <span className="graph-node-lang" style={{ color: style.text }}>
                {lang}
              </span>
            </div>
          ),
        },
        style: {
          background: style.bg,
          color: style.text,
          border: isSelected
            ? `3px solid ${style.bg}`
            : isEntry
            ? "2px solid #16a76e"
            : inCycle
            ? "2px solid #e5484d"
            : "2px solid rgba(255,255,255,0.25)",
          borderRadius: "12px",
          padding: "10px 14px",
          fontSize: "12px",
          fontWeight: "600",
          fontFamily: "'Inter', sans-serif",
          width: NODE_WIDTH,
          boxShadow: isSelected
            ? `0 0 0 4px ${style.bg}30, 0 4px 16px rgba(0,0,0,0.12)`
            : "0 2px 8px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06)",
          transition: "all 0.25s ease",
          cursor: "pointer",
        },
      };
    });

    const rawEdges = (graphData.edges || []).map((edge) => {
      const isHighlighted =
        selectedNode === edge.source || selectedNode === edge.target;

      return {
        ...edge,
        animated: isHighlighted,
        style: {
          stroke: isHighlighted ? "#5b5fc7" : "#c4c7d4",
          strokeWidth: isHighlighted ? 2.5 : 1.5,
          transition: "all 0.25s ease",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isHighlighted ? "#5b5fc7" : "#c4c7d4",
          width: 14,
          height: 14,
        },
      };
    });

    const { nodes: ln, edges: le } = getLayoutedElements(rawNodes, rawEdges);
    return { layoutedNodes: ln, layoutedEdges: le };
  }, [graphData, selectedNode, entrySet, cycleFiles]);

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  useEffect(() => {
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_, node) => {
      if (onNodeClick) {
        onNodeClick(node.id);
      }
    },
    [onNodeClick]
  );

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="graph-empty" id="dependency-graph">
        <div className="graph-empty-content">
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="12" r="8" stroke="#5b5fc7" strokeWidth="2" fill="#5b5fc710" />
            <circle cx="20" cy="48" r="8" stroke="#5b5fc7" strokeWidth="2" fill="#5b5fc710" />
            <circle cx="60" cy="48" r="8" stroke="#5b5fc7" strokeWidth="2" fill="#5b5fc710" />
            <line x1="36" y1="20" x2="24" y2="40" stroke="#5b5fc740" strokeWidth="2" />
            <line x1="44" y1="20" x2="56" y2="40" stroke="#5b5fc740" strokeWidth="2" />
          </svg>
          <p>Analyze a repository to see the dependency tree</p>
        </div>
      </div>
    );
  }

  return (
    <div className="graph-container" id="dependency-graph">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.15}
        maxZoom={2}
        attributionPosition="bottom-left"
      >
        <Background color="#e2e4ec" gap={24} size={1} />
        <Controls className="graph-controls" showInteractive={false} />
        <MiniMap
          nodeColor={(node) => {
            const lang = node.data?.language || "unknown";
            return (LANG_STYLES[lang] || LANG_STYLES.unknown).mini;
          }}
          maskColor="rgba(248, 249, 252, 0.85)"
          className="graph-minimap"
        />
      </ReactFlow>
      <div className="graph-stats">
        <span>{graphData.nodes.length} files</span>
        <span>•</span>
        <span>{graphData.edges.length} dependencies</span>
        {cycles.length > 0 && (
          <>
            <span>•</span>
            <span className="cycle-warning">⚠️ {cycles.length} cycles</span>
          </>
        )}
      </div>
    </div>
  );
}
