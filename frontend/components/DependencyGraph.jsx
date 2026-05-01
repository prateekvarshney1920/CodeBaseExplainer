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
import "reactflow/dist/style.css";

/** Language → color for minimap and highlighting */
const LANG_COLORS = {
  python: "#3776AB",
  javascript: "#F7DF1E",
  typescript: "#3178C6",
  java: "#ED8B00",
  go: "#00ADD8",
  cpp: "#00599C",
  c: "#A8B9CC",
  csharp: "#239120",
  ruby: "#CC342D",
  rust: "#DEA584",
  unknown: "#6B7280",
};

/**
 * DependencyGraph — Interactive graph visualization using React Flow.
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

  // Prepare nodes with styling
  const initialNodes = useMemo(() => {
    if (!graphData?.nodes) return [];

    return graphData.nodes.map((node) => {
      const lang = node.data?.language || "unknown";
      const color = LANG_COLORS[lang] || LANG_COLORS.unknown;
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
              <span
                className="graph-node-lang"
                style={{ color: lang === "javascript" ? "#000" : "#fff" }}
              >
                {lang}
              </span>
            </div>
          ),
        },
        style: {
          background: isSelected
            ? `linear-gradient(135deg, ${color}dd, ${color}99)`
            : `linear-gradient(135deg, ${color}88, ${color}55)`,
          color: lang === "javascript" ? "#000" : "#fff",
          border: isSelected
            ? `3px solid ${color}`
            : isEntry
            ? "2px solid #10b981"
            : inCycle
            ? "2px solid #ef4444"
            : "2px solid rgba(255,255,255,0.15)",
          borderRadius: "12px",
          padding: "12px 16px",
          fontSize: "12px",
          fontWeight: "600",
          width: 180,
          boxShadow: isSelected
            ? `0 0 20px ${color}66`
            : "0 4px 12px rgba(0,0,0,0.3)",
          transition: "all 0.3s ease",
          cursor: "pointer",
        },
      };
    });
  }, [graphData, selectedNode, entrySet, cycleFiles]);

  // Prepare edges
  const initialEdges = useMemo(() => {
    if (!graphData?.edges) return [];

    return graphData.edges.map((edge) => {
      const isHighlighted =
        selectedNode === edge.source || selectedNode === edge.target;

      return {
        ...edge,
        animated: isHighlighted,
        style: {
          stroke: isHighlighted ? "#818cf8" : "#6366f180",
          strokeWidth: isHighlighted ? 3 : 1.5,
          transition: "all 0.3s ease",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isHighlighted ? "#818cf8" : "#6366f180",
          width: 16,
          height: 16,
        },
      };
    });
  }, [graphData, selectedNode]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update when data changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

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
            <circle cx="20" cy="20" r="8" stroke="#6366f1" strokeWidth="2" fill="#6366f133" />
            <circle cx="60" cy="20" r="8" stroke="#6366f1" strokeWidth="2" fill="#6366f133" />
            <circle cx="40" cy="60" r="8" stroke="#6366f1" strokeWidth="2" fill="#6366f133" />
            <line x1="26" y1="24" x2="34" y2="54" stroke="#6366f155" strokeWidth="2" />
            <line x1="54" y1="24" x2="46" y2="54" stroke="#6366f155" strokeWidth="2" />
            <line x1="28" y1="20" x2="52" y2="20" stroke="#6366f155" strokeWidth="2" />
          </svg>
          <p>Analyze a repository to see the dependency graph</p>
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
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        attributionPosition="bottom-left"
      >
        <Background color="#6366f122" gap={20} size={1} />
        <Controls
          className="graph-controls"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={(node) => {
            const lang = node.data?.language || "unknown";
            return LANG_COLORS[lang] || LANG_COLORS.unknown;
          }}
          maskColor="rgba(0, 0, 0, 0.7)"
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
