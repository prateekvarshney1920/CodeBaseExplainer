"""
Entry Point Detector — Identifies likely entry point files in a codebase.
Uses filename heuristics, graph topology, and import hub analysis.
"""

import logging
from typing import Dict, List, Any, Set
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

# Common entry point filenames (case-insensitive basenames)
ENTRY_POINT_NAMES = {
    "main.py", "app.py", "server.py", "wsgi.py", "asgi.py",
    "manage.py", "__main__.py", "run.py", "cli.py",
    "index.js", "index.ts", "index.jsx", "index.tsx",
    "app.js", "app.ts", "app.jsx", "app.tsx",
    "server.js", "server.ts",
    "main.js", "main.ts", "main.go", "main.rs",
    "main.java", "main.c", "main.cpp",
    "program.cs", "startup.cs",
}

# Patterns that suggest an entry point (in the filename path)
ENTRY_POINT_PATTERNS = [
    "src/index",
    "src/main",
    "src/app",
    "cmd/",
    "bin/",
]


def detect_entry_points(
    parsed_files: Dict[str, Dict],
    graph_data: Dict[str, Any],
) -> List[str]:
    """
    Detect entry point files using multiple heuristics.

    Args:
        parsed_files: Dict mapping filename → parsed data
        graph_data: Graph data with nodes and edges

    Returns:
        Sorted list of detected entry point filenames
    """
    entry_points: Set[str] = set()
    all_files = set(parsed_files.keys())

    # 1. Filename heuristics
    for filename in all_files:
        basename = PurePosixPath(filename).name.lower()
        if basename in ENTRY_POINT_NAMES:
            entry_points.add(filename)
            continue
        # Check path patterns
        for pattern in ENTRY_POINT_PATTERNS:
            if pattern in filename.lower():
                entry_points.add(filename)
                break

    # 2. Files with no incoming edges (nothing imports them)
    targets = set()
    for edge in graph_data.get("edges", []):
        targets.add(edge["target"])

    for filename in all_files:
        if filename not in targets:
            # This file is not imported by anything — potential entry point
            # But only if it imports at least one other file (not isolated)
            file_imports = [
                e for e in graph_data.get("edges", [])
                if e["source"] == filename
            ]
            if file_imports:
                entry_points.add(filename)

    # 3. Hub files — files that import the most other files
    import_counts: Dict[str, int] = {}
    for edge in graph_data.get("edges", []):
        src = edge["source"]
        import_counts[src] = import_counts.get(src, 0) + 1

    if import_counts:
        max_imports = max(import_counts.values())
        threshold = max(max_imports * 0.7, 3)
        for filename, count in import_counts.items():
            if count >= threshold:
                entry_points.add(filename)

    # 4. Check for __name__ == "__main__" pattern (Python)
    for filename, data in parsed_files.items():
        if data.get("language") == "python":
            # We don't have the content here, but the filename check
            # already covers most Python entry points
            pass

    result = sorted(entry_points)
    logger.info(f"Detected {len(result)} entry points: {result}")
    return result
