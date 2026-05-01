"""
Agent Service — AI Agent that orchestrates codebase analysis.
Uses a goal → steps → execution pattern to understand a codebase.
"""

import logging
from typing import Dict, List, Any

from engine.parser import parse_file, detect_language
from engine.graph_builder import DependencyGraph
from engine.entry_point_detector import detect_entry_points
from services.llm_service import summarize_file, explain_architecture

logger = logging.getLogger(__name__)


class CodebaseAgent:
    """
    AI Agent that analyzes a codebase through a structured pipeline:
    detect_language → parse_files → build_graph → summarize_files → generate_overview
    """

    def __init__(self, repo_data: Dict[str, str]):
        """
        Args:
            repo_data: Dictionary mapping {filename: content}
        """
        self.repo_data = repo_data
        self.steps: List[str] = []
        self.results: Dict[str, Any] = {}

    def plan(self):
        """Define the analysis steps."""
        self.steps = [
            "detect_language",
            "parse_files",
            "build_graph",
            "detect_entry_points",
            "summarize_files",
            "generate_overview",
        ]
        logger.info(f"Agent planned {len(self.steps)} steps: {self.steps}")

    def execute(self) -> Dict[str, Any]:
        """Execute each planned step and accumulate results."""
        for step in self.steps:
            logger.info(f"Agent executing step: {step}")
            try:
                handler = getattr(self, f"_step_{step}")
                handler()
                logger.info(f"Step '{step}' completed successfully")
            except Exception as e:
                logger.error(f"Step '{step}' failed: {e}")
                self.results[f"{step}_error"] = str(e)
        return self.results

    def run(self) -> Dict[str, Any]:
        """Plan and execute all steps, return results."""
        self.plan()
        return self.execute()

    # ── Step implementations ───────────────────────────────────────────────

    def _step_detect_language(self):
        """Detect the primary languages in the codebase."""
        lang_counts: Dict[str, int] = {}
        for filename in self.repo_data:
            lang = detect_language(filename)
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        self.results["languages"] = lang_counts
        self.results["primary_language"] = max(lang_counts, key=lang_counts.get) if lang_counts else "unknown"

    def _step_parse_files(self):
        """Parse all files to extract imports, exports, and declarations."""
        parsed = {}
        for filename, content in self.repo_data.items():
            try:
                parsed[filename] = parse_file(filename, content)
            except Exception as e:
                logger.warning(f"Failed to parse {filename}: {e}")
                parsed[filename] = {
                    "filename": filename,
                    "language": detect_language(filename),
                    "imports": [],
                    "exports": [],
                    "declarations": [],
                    "error": str(e),
                }
        self.results["parsed_files"] = parsed

    def _step_build_graph(self):
        """Build the dependency graph from parsed files."""
        parsed_files = self.results.get("parsed_files", {})
        graph = DependencyGraph()
        graph_data = graph.build(parsed_files)
        self.results["graph"] = graph_data
        self.results["cycles"] = graph.detect_cycles()
        self.results["_graph_instance"] = graph

    def _step_detect_entry_points(self):
        """Detect entry point files."""
        parsed_files = self.results.get("parsed_files", {})
        graph_data = self.results.get("graph", {"nodes": [], "edges": []})
        entry_points = detect_entry_points(parsed_files, graph_data)
        self.results["entry_points"] = entry_points

        # Update graph data with entry points and cycles
        graph_data["entry_points"] = entry_points
        graph_data["cycles"] = self.results.get("cycles", [])

    def _step_summarize_files(self):
        """Generate LLM summaries for each file."""
        summaries = {}
        for filename, content in self.repo_data.items():
            try:
                # Truncate very large files for LLM context
                truncated = content[:8000] if len(content) > 8000 else content
                summary = summarize_file(filename, truncated)
                summaries[filename] = summary
            except Exception as e:
                logger.warning(f"Failed to summarize {filename}: {e}")
                summaries[filename] = f"[Summary unavailable: {str(e)}]"

        self.results["summaries"] = summaries

        # Inject summaries into graph nodes
        graph = self.results.get("graph", {})
        for node in graph.get("nodes", []):
            node_id = node["id"]
            if node_id in summaries:
                node["data"]["summary"] = summaries[node_id]

    def _step_generate_overview(self):
        """Generate an overall architecture overview."""
        # Build file tree string
        file_tree = "\n".join(sorted(self.repo_data.keys()))

        # Build dependency summary
        graph = self.results.get("graph", {})
        dep_lines = []
        for edge in graph.get("edges", []):
            dep_lines.append(f"{edge['source']} → {edge['target']}")
        deps = "\n".join(dep_lines) if dep_lines else "No dependencies detected"

        # Entry points
        entry_points = ", ".join(self.results.get("entry_points", []))

        try:
            overview = explain_architecture(file_tree, deps, entry_points)
            self.results["architecture_overview"] = overview
        except Exception as e:
            logger.error(f"Failed to generate architecture overview: {e}")
            self.results["architecture_overview"] = f"[Architecture overview unavailable: {str(e)}]"
