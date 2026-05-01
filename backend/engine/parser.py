"""
Parser — Extracts imports, exports, and declarations from source files.
Uses tree-sitter for accurate parsing with regex fallback.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ── Language detection ─────────────────────────────────────────────────────────

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".rs": "rust",
    ".h": "c",
    ".hpp": "cpp",
}


def detect_language(filename: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(filename).suffix.lower()
    return EXTENSION_MAP.get(ext, "unknown")


# ── Tree-sitter parsing ───────────────────────────────────────────────────────

_TS_AVAILABLE = False
_ts_parsers = {}

try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    from tree_sitter import Language, Parser

    _TS_AVAILABLE = True

    PY_LANGUAGE = Language(tspython.language())
    JS_LANGUAGE = Language(tsjavascript.language())

    _ts_lang_map = {
        "python": PY_LANGUAGE,
        "javascript": JS_LANGUAGE,
    }

    logger.info("tree-sitter loaded successfully")
except ImportError as e:
    logger.warning(f"tree-sitter not available, using regex fallback: {e}")
except Exception as e:
    logger.warning(f"tree-sitter initialization failed, using regex fallback: {e}")


def _get_ts_parser(language: str) -> Optional[Any]:
    """Get or create a tree-sitter parser for the given language."""
    if not _TS_AVAILABLE:
        return None
    if language not in _ts_lang_map:
        return None
    if language not in _ts_parsers:
        parser = Parser(_ts_lang_map[language])
        _ts_parsers[language] = parser
    return _ts_parsers[language]


def _parse_with_tree_sitter(filename: str, content: str, language: str) -> Optional[Dict]:
    """Parse a file using tree-sitter. Returns None if unavailable."""
    parser = _get_ts_parser(language)
    if parser is None:
        return None

    try:
        tree = parser.parse(content.encode("utf-8"))
        root = tree.root_node

        imports = []
        exports = []
        declarations = []

        if language == "python":
            imports, exports, declarations = _extract_python_ts(root, content)
        elif language == "javascript":
            imports, exports, declarations = _extract_javascript_ts(root, content)
        else:
            return None

        return {
            "filename": filename,
            "language": language,
            "imports": imports,
            "exports": exports,
            "declarations": declarations,
        }
    except Exception as e:
        logger.warning(f"tree-sitter parse failed for {filename}: {e}")
        return None


def _extract_python_ts(root, content: str):
    """Extract Python imports, exports, and declarations via tree-sitter."""
    imports = []
    exports = []
    declarations = []

    def walk(node):
        if node.type == "import_statement":
            text = content[node.start_byte:node.end_byte]
            match = re.search(r"import\s+(\S+)", text)
            if match:
                imports.append(match.group(1))
        elif node.type == "import_from_statement":
            text = content[node.start_byte:node.end_byte]
            match = re.search(r"from\s+(\S+)\s+import", text)
            if match:
                imports.append(match.group(1))
            # Exported names from this import
            name_matches = re.findall(r"import\s+(.+)", text)
            if name_matches:
                for name in name_matches[0].split(","):
                    name = name.strip().split(" as ")[0].strip()
                    if name and name != "*":
                        pass  # These are imports, not exports
        elif node.type == "function_definition":
            # Get function name
            for child in node.children:
                if child.type == "identifier":
                    name = content[child.start_byte:child.end_byte]
                    declarations.append(name)
                    # Top-level functions are considered exports in Python
                    if node.parent and node.parent.type == "module":
                        exports.append(name)
                    break
        elif node.type == "class_definition":
            for child in node.children:
                if child.type == "identifier":
                    name = content[child.start_byte:child.end_byte]
                    declarations.append(name)
                    if node.parent and node.parent.type == "module":
                        exports.append(name)
                    break

        for child in node.children:
            walk(child)

    walk(root)
    return imports, exports, declarations


def _extract_javascript_ts(root, content: str):
    """Extract JavaScript/JSX imports, exports, and declarations via tree-sitter."""
    imports = []
    exports = []
    declarations = []

    def walk(node):
        if node.type == "import_statement":
            text = content[node.start_byte:node.end_byte]
            match = re.search(r"""from\s+['"]([^'"]+)['"]""", text)
            if match:
                imports.append(match.group(1))
            else:
                match = re.search(r"""import\s+['"]([^'"]+)['"]""", text)
                if match:
                    imports.append(match.group(1))
        elif node.type == "export_statement":
            text = content[node.start_byte:node.end_byte]
            # export default function/class name
            match = re.search(r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)", text)
            if match:
                exports.append(match.group(1))
                declarations.append(match.group(1))
        elif node.type in ("function_declaration", "generator_function_declaration"):
            for child in node.children:
                if child.type == "identifier":
                    name = content[child.start_byte:child.end_byte]
                    declarations.append(name)
                    break
        elif node.type == "class_declaration":
            for child in node.children:
                if child.type == "identifier":
                    name = content[child.start_byte:child.end_byte]
                    declarations.append(name)
                    break
        elif node.type == "lexical_declaration":
            # const/let declarations
            for child in node.children:
                if child.type == "variable_declarator":
                    for vchild in child.children:
                        if vchild.type == "identifier":
                            name = content[vchild.start_byte:vchild.end_byte]
                            declarations.append(name)
                            break
        elif node.type == "call_expression":
            # Detect require('...') calls
            text = content[node.start_byte:node.end_byte]
            match = re.search(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", text)
            if match:
                imports.append(match.group(1))

        for child in node.children:
            walk(child)

    walk(root)
    return imports, exports, declarations


# ── Regex fallback parsers ─────────────────────────────────────────────────────

def _parse_python_regex(content: str) -> tuple:
    """Regex-based Python parser (fallback)."""
    imports = []
    exports = []
    declarations = []

    for line in content.split("\n"):
        line = line.strip()
        # Import statements
        match = re.match(r"^import\s+(\S+)", line)
        if match:
            imports.append(match.group(1))
            continue
        match = re.match(r"^from\s+(\S+)\s+import", line)
        if match:
            imports.append(match.group(1))
            continue
        # Function definitions
        match = re.match(r"^def\s+(\w+)\s*\(", line)
        if match:
            name = match.group(1)
            declarations.append(name)
            if not name.startswith("_"):
                exports.append(name)
            continue
        # Class definitions
        match = re.match(r"^class\s+(\w+)[\s:(]", line)
        if match:
            name = match.group(1)
            declarations.append(name)
            exports.append(name)
            continue

    return imports, exports, declarations


def _parse_javascript_regex(content: str) -> tuple:
    """Regex-based JavaScript/TypeScript parser (fallback)."""
    imports = []
    exports = []
    declarations = []

    for line in content.split("\n"):
        line = line.strip()
        # import ... from '...'
        match = re.search(r"""from\s+['"]([^'"]+)['"]""", line)
        if match and ("import" in line):
            imports.append(match.group(1))
            continue
        # import '...'
        match = re.match(r"""^import\s+['"]([^'"]+)['"]""", line)
        if match:
            imports.append(match.group(1))
            continue
        # require('...')
        match = re.search(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", line)
        if match:
            imports.append(match.group(1))
            continue
        # export function/class/const
        match = re.match(r"^export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)", line)
        if match:
            name = match.group(1)
            exports.append(name)
            declarations.append(name)
            continue
        # function/class declarations
        match = re.match(r"^(?:async\s+)?function\s+(\w+)", line)
        if match:
            declarations.append(match.group(1))
            continue
        match = re.match(r"^class\s+(\w+)", line)
        if match:
            declarations.append(match.group(1))
            continue
        # const/let/var declarations at top level
        match = re.match(r"^(?:const|let|var)\s+(\w+)", line)
        if match:
            declarations.append(match.group(1))
            continue

    return imports, exports, declarations


def _parse_java_regex(content: str) -> tuple:
    """Regex-based Java parser."""
    imports = []
    exports = []
    declarations = []

    for line in content.split("\n"):
        line = line.strip()
        match = re.match(r"^import\s+([\w.]+);", line)
        if match:
            imports.append(match.group(1))
            continue
        match = re.match(r"^(?:public\s+)?(?:abstract\s+)?class\s+(\w+)", line)
        if match:
            name = match.group(1)
            declarations.append(name)
            exports.append(name)
            continue
        match = re.match(r"^(?:public\s+)?interface\s+(\w+)", line)
        if match:
            name = match.group(1)
            declarations.append(name)
            exports.append(name)
            continue
        match = re.match(r"\s*(?:public|protected|private)\s+.*?\s+(\w+)\s*\(", line)
        if match:
            declarations.append(match.group(1))

    return imports, exports, declarations


def _parse_generic_regex(content: str) -> tuple:
    """Very basic regex parser for other languages (Go, Rust, C, etc.)."""
    imports = []
    exports = []
    declarations = []

    for line in content.split("\n"):
        line = line.strip()
        # Generic import patterns
        match = re.search(r"""#include\s*[<"]([^>"]+)[>"]""", line)
        if match:
            imports.append(match.group(1))
            continue
        match = re.match(r"^use\s+([\w:]+)", line)  # Rust
        if match:
            imports.append(match.group(1))
            continue
        # Go imports
        match = re.match(r'^import\s+"([^"]+)"', line)
        if match:
            imports.append(match.group(1))
            continue
        # Function declarations
        match = re.match(r"^(?:pub\s+)?fn\s+(\w+)", line)  # Rust
        if match:
            declarations.append(match.group(1))
            continue
        match = re.match(r"^func\s+(\w+)", line)  # Go
        if match:
            declarations.append(match.group(1))
            continue

    return imports, exports, declarations


# ── Public API ─────────────────────────────────────────────────────────────────

REGEX_PARSERS = {
    "python": _parse_python_regex,
    "javascript": _parse_javascript_regex,
    "typescript": _parse_javascript_regex,
    "java": _parse_java_regex,
}


def parse_file(filename: str, content: str) -> Dict[str, Any]:
    """
    Parse a source file to extract imports, exports, and declarations.
    Uses tree-sitter when available, falls back to regex.
    """
    language = detect_language(filename)

    # Try tree-sitter first
    result = _parse_with_tree_sitter(filename, content, language)
    if result is not None:
        return result

    # Fallback to regex
    parser = REGEX_PARSERS.get(language, _parse_generic_regex)
    imports, exports, declarations = parser(content)

    return {
        "filename": filename,
        "language": language,
        "imports": imports,
        "exports": exports,
        "declarations": declarations,
    }
