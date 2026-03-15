"""
Tests for agent/troubleshooter.py
"""

import pytest

from agent.troubleshooter import NODES, run_tree, START_MENU


class TestNodes:
    def test_start_node_exists(self):
        assert "start" in NODES

    def test_start_node_has_choices(self):
        assert len(NODES["start"].choices) >= 4

    def test_all_choices_point_to_valid_nodes(self):
        for node_id, node in NODES.items():
            for choice_label, target_id in node.choices.items():
                assert target_id in NODES, (
                    f"Node '{node_id}' choice '{choice_label}' "
                    f"points to unknown node '{target_id}'"
                )

    def test_terminal_nodes_have_advice(self):
        terminal = [n for n in NODES.values() if not n.choices]
        assert len(terminal) >= 5
        for node in terminal:
            assert len(node.advice) > 0, f"Terminal node '{node.id}' has no advice"

    def test_start_menu_keys_match_start_node(self):
        # START_MENU values should all point to nodes
        for key, (label, nid) in START_MENU.items():
            assert nid in NODES, f"START_MENU entry '{key}' → '{nid}' not found in NODES"


class TestRunTree:
    def _make_runner(self, responses):
        """Return ask_fn and print_fn that drive the tree with canned responses."""
        idx = [0]
        printed = []

        def ask_fn(prompt, choices):
            choice = responses[idx[0]] if idx[0] < len(responses) else "q"
            idx[0] += 1
            return choice

        def print_fn(lines):
            printed.extend(lines)

        return ask_fn, print_fn, printed

    def test_quit_from_start(self):
        ask_fn, print_fn, printed = self._make_runner(["q"])
        run_tree(ask_fn, print_fn)   # should not raise

    def test_navigation_to_terminal(self):
        # Navigate: start → bsod → bsod_known_code → bsod_memory → quit
        ask_fn, print_fn, printed = self._make_runner(["1", "1", "1", "q"])
        run_tree(ask_fn, print_fn)
        joined = "\n".join(printed)
        assert "RAM" in joined or "MemTest" in joined

    def test_restart_from_terminal(self):
        # Navigate to a terminal, press 'r' to restart, then quit
        ask_fn, print_fn, printed = self._make_runner(["5", "r", "q"])
        run_tree(ask_fn, print_fn)   # should not raise or loop infinitely

    def test_no_display_path(self):
        ask_fn, print_fn, printed = self._make_runner(["4", "q"])
        run_tree(ask_fn, print_fn)
        joined = "\n".join(printed)
        assert "display" in joined.lower() or "GPU" in joined or "monitor" in joined.lower()
