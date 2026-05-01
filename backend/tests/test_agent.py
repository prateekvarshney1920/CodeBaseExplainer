"""
Tests for the CodebaseAgent.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from services.agent_service import CodebaseAgent


MOCK_REPO = {
    "src/main.py": """
import os
from src.utils import helper

def main():
    helper()

if __name__ == "__main__":
    main()
""",
    "src/utils.py": """
import json

def helper():
    return "helping"

class DataLoader:
    pass
""",
    "src/app.js": """
import React from 'react';
import { helper } from './utils';

export default function App() {
    return <div>Hello</div>;
}
""",
    "src/utils.js": """
export function helper() {
    return "helping";
}

export const VERSION = "1.0";
""",
}


class TestCodebaseAgent:
    def test_plan_creates_steps(self):
        agent = CodebaseAgent(MOCK_REPO)
        agent.plan()
        assert len(agent.steps) == 6
        assert "detect_language" in agent.steps
        assert "parse_files" in agent.steps
        assert "build_graph" in agent.steps
        assert "summarize_files" in agent.steps

    @patch("services.agent_service.summarize_file")
    @patch("services.agent_service.explain_architecture")
    def test_run_produces_results(self, mock_arch, mock_summary):
        mock_summary.return_value = "This is a test summary."
        mock_arch.return_value = "This is an architecture overview."

        agent = CodebaseAgent(MOCK_REPO)
        results = agent.run()

        assert "languages" in results
        assert "parsed_files" in results
        assert "graph" in results
        assert "summaries" in results
        assert "architecture_overview" in results
        assert "entry_points" in results

    @patch("services.agent_service.summarize_file")
    @patch("services.agent_service.explain_architecture")
    def test_language_detection(self, mock_arch, mock_summary):
        mock_summary.return_value = "Summary."
        mock_arch.return_value = "Overview."

        agent = CodebaseAgent(MOCK_REPO)
        results = agent.run()

        langs = results["languages"]
        assert "python" in langs
        assert "javascript" in langs

    @patch("services.agent_service.summarize_file")
    @patch("services.agent_service.explain_architecture")
    def test_graph_has_nodes_and_edges(self, mock_arch, mock_summary):
        mock_summary.return_value = "Summary."
        mock_arch.return_value = "Overview."

        agent = CodebaseAgent(MOCK_REPO)
        results = agent.run()

        graph = results["graph"]
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 4  # 4 files

    @patch("services.agent_service.summarize_file")
    @patch("services.agent_service.explain_architecture")
    def test_entry_points_detected(self, mock_arch, mock_summary):
        mock_summary.return_value = "Summary."
        mock_arch.return_value = "Overview."

        agent = CodebaseAgent(MOCK_REPO)
        results = agent.run()

        entry_points = results["entry_points"]
        assert isinstance(entry_points, list)
        # main.py should be detected as entry point
        assert any("main.py" in ep for ep in entry_points)

    def test_empty_repo(self):
        agent = CodebaseAgent({})
        agent.plan()
        assert len(agent.steps) == 6
