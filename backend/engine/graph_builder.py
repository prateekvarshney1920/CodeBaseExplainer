"""
Graph Builder — Constructs a dependency graph from parsed source files.
Output is compatible with React Flow for frontend visualization.
"""

import logging
import math
from typing import Dict, List, Any, Set, Tuple
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

# Language → color mapping for graph nodes
LANGUAGE_COLORS = {
    "python": "#3776AB",
    "javascript": "#F7DF1E",
    "typescript": "#3178C6",
    "java": "#ED8B00",
    "go": "#00ADD8",
    "cpp": "#00599C",
    "c": "#A8B9CC",
    "csharp": "#239120",
    "ruby": "#CC342D",
    "rust": "#DEA584",
    "unknown": "#6B7280",
}


class DependencyGraph:
    """
    Builds and manages a dependency graph from parsed source files.
    Nodes represent files, edges represent import relationships.
    """

    def __init__(self):
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []
        self.adjacency: Dict[str, Dict[str, List[str]]] = {}
        self._file_set: Set[str] = set()

    def build(self, parsed_files: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Build the dependency graph from parsed file data.

        Args:
            parsed_files: Dict mapping filename → parsed data dict
                          (with 'imports', 'exports', 'declarations', 'language')

        Returns:
            Graph data compatible with React Flow:
            {nodes: [...], edges: [...], cycles: [], entry_points: []}
        """
        self._file_set = set(parsed_files.keys())
        self.nodes = []
        self.edges = []
        self.adjacency = {}

        # Create nodes
        for filename, data in parsed_files.items():
            language = data.get("language", "unknown")
            self.nodes.append({
                "id": filename,
                "type": "default",
                "data": {
                    "label": PurePosixPath(filename).name,
                    "fullPath": filename,
                    "language": language,
                    "imports": data.get("imports", []),
                    "exports": data.get("exports", []),
                    "declarations": data.get("declarations", []),
                    "summary": "",
                },
                "position": {"x": 0, "y": 0},
                "style": {
                    "background": LANGUAGE_COLORS.get(language, LANGUAGE_COLORS["unknown"]),
                    "color": "#fff" if language not in ("javascript",) else "#000",
                    "border": "2px solid rgba(255,255,255,0.2)",
                    "borderRadius": "12px",
                    "padding": "10px",
                    "fontSize": "12px",
                    "fontWeight": "600",
                    "width": 180,
                },
            })
            self.adjacency[filename] = {"imports": [], "imported_by": []}

        # Create edges by resolving imports
        edge_id = 0
        for filename, data in parsed_files.items():
            for imp in data.get("imports", []):
                resolved = self._resolve_import(filename, imp)
                if resolved and resolved in self._file_set:
                    edge_id += 1
                    self.edges.append({
                        "id": f"e{edge_id}",
                        "source": filename,
                        "target": resolved,
                        "animated": True,
                        "style": {"stroke": "#6366f1", "strokeWidth": 2},
                        "type": "smoothstep",
                    })
                    self.adjacency[filename]["imports"].append(resolved)
                    if resolved in self.adjacency:
                        self.adjacency[resolved]["imported_by"].append(filename)

        # Calculate layout positions
        self._calculate_positions()

        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "cycles": [],
            "entry_points": [],
        }

    def _resolve_import(self, source_file: str, import_path: str) -> str | None:
        """
        Resolve an import string to an actual file in the repository.
        Handles relative imports (./foo, ../bar) and module imports.
        """
        # Handle relative imports
        if import_path.startswith("."):
            source_dir = str(PurePosixPath(source_file).parent)
            if source_dir == ".":
                source_dir = ""

            # Resolve the relative path
            if import_path.startswith("./"):
                candidate_base = f"{source_dir}/{import_path[2:]}" if source_dir else import_path[2:]
            elif import_path.startswith("../"):
                parts = source_dir.split("/") if source_dir else []
                import_parts = import_path.split("/")
                up_count = 0
                for p in import_parts:
                    if p == "..":
                        up_count += 1
                    else:
                        break
                remaining = "/".join(import_parts[up_count:])
                base_parts = parts[:-up_count] if up_count <= len(parts) else []
                candidate_base = "/".join(base_parts + [remaining]) if base_parts else remaining
            else:
                candidate_base = import_path.lstrip(".")
                if source_dir:
                    candidate_base = f"{source_dir}/{candidate_base}"

            return self._find_file(candidate_base)

        # Handle absolute/module imports (Python style: dotted path)
        module_path = import_path.replace(".", "/")
        result = self._find_file(module_path)
        if result:
            return result

        # Try as-is
        return self._find_file(import_path)

    def _find_file(self, base_path: str) -> str | None:
        """Try to find a file matching the base path with various extensions."""
        # Direct match
        if base_path in self._file_set:
            return base_path

        # Try common extensions
        extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"]
        for ext in extensions:
            candidate = f"{base_path}{ext}"
            if candidate in self._file_set:
                return candidate

        # Try index files (JS/TS convention)
        for idx in ["index.js", "index.ts", "index.jsx", "index.tsx"]:
            candidate = f"{base_path}/{idx}"
            if candidate in self._file_set:
                return candidate

        # Try __init__.py (Python convention)
        candidate = f"{base_path}/__init__.py"
        if candidate in self._file_set:
            return candidate

        return None

    def _calculate_positions(self):
        """Calculate node positions using a layered layout algorithm."""
        if not self.nodes:
            return

        # Group nodes by directory depth for layering
        layers: Dict[int, List[int]] = {}
        for i, node in enumerate(self.nodes):
            depth = node["id"].count("/")
            if depth not in layers:
                layers[depth] = []
            layers[depth].append(i)

        # Position nodes
        y_offset = 0
        x_spacing = 280
        y_spacing = 150

        for depth in sorted(layers.keys()):
            indices = layers[depth]
            total_width = len(indices) * x_spacing
            x_start = -(total_width / 2) + (x_spacing / 2)

            for j, idx in enumerate(indices):
                self.nodes[idx]["position"] = {
                    "x": int(x_start + j * x_spacing),
                    "y": int(y_offset),
                }
            y_offset += y_spacing

    def get_adjacency(self, filename: str) -> Dict[str, List[str]]:
        """
        Get adjacent files for a given filename.

        Returns:
            Dict with 'imports' (files this file imports)
            and 'imported_by' (files that import this file)
        """
        return self.adjacency.get(filename, {"imports": [], "imported_by": []})

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies using DFS.

        Returns:
            List of cycles, where each cycle is a list of filenames.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.adjacency.get(node, {}).get("imports", []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.discard(node)

        for node in self.adjacency:
            if node not in visited:
                dfs(node)

        return cycles
