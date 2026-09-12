# SPDX-License-Identifier: LGPL-2.1-or-later

"""Live Qt coverage for bounded usage rendering with long histories."""

import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide import QtCore, QtWidgets
import VibeCADGui as gui
from VibeCADTokenUsage import TokenUsageAccumulator

class TestUsageSummaryGui(unittest.TestCase):
    def test_real_widgets_long_history_toggle_and_graph(self):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        output = QtWidgets.QTextBrowser(panel)
        output.setObjectName("VibeConversation")
        toggle = QtWidgets.QToolButton(panel)
        toggle.setObjectName("VibeUsageSummaryToggle")
        toggle.setCheckable(True)
        scroll = gui._make_usage_summary_widget(panel)
        details = scroll.findChild(QtWidgets.QLabel, "VibeUsageSummaryDetails")
        for widget in (toggle, scroll, output):
            layout.addWidget(widget)
        panel.resize(900, 800)
        panel.show()
        self.addCleanup(panel.close)
        accumulator = TokenUsageAccumulator(provider="openai", auth_mode="api_key")
        accumulator.set_thread_id("smoke-thread")
        accumulator.set_model("reported-model", source="transport")
        entries=[]
        for i in range(1000):
            accumulator.set_active_turn(f"turn-{i}")
            accumulator.observe({"threadId": "smoke-thread", "turnId": f"turn-{i}",
                "tokenUsage": {"last": {"inputTokens": 100, "cachedInputTokens": 20,
                    "outputTokens": 10, "reasoningOutputTokens": 2, "totalTokens": 110}}})
            entries.append({"role": "assistant", "sequence": i+1, "content": "Synthetic reply",
                            "metadata": {"usage": accumulator.metadata(status="completed")}})
        output.setProperty("VibeConversationEntries", entries)
        original = gui._conversation_usage_entries
        with patch.object(gui, "_conversation_usage_entries", wraps=original) as reads:
            start=time.perf_counter()
            for i in range(100):
                gui._render_usage_summary(panel)
            collapsed=time.perf_counter()-start
            self.assertEqual(reads.call_count, 0)
            toggle.setChecked(True)
            start=time.perf_counter()
            gui._render_usage_summary(panel)
            expanded=time.perf_counter()-start
            self.assertEqual(reads.call_count, 1)
        graph=panel.findChild(QtWidgets.QWidget, "VibeUsageGraph")
        self.assertIsNotNone(graph)
        self.assertFalse(graph.isHidden())
        self.assertFalse(details.isHidden())
        self.assertFalse(scroll.isHidden())
        self.assertLessEqual(scroll.height(), 280)
        self.assertIn("reported-model", details.text())
        self.assertIn("110,000", details.text())
        QtWidgets.QApplication.processEvents()
        self.assertLessEqual(panel.height(), 1000, "Usage must not expand the conversation window")
        screenshot=panel.grab()
        self.assertFalse(screenshot.isNull())
        artifact_dir = os.environ.get("VIBECAD_TEST_OUTPUT")
        if artifact_dir:
            screenshot.save(str(Path(artifact_dir) / "usage-graph.png"))
        toggle.setChecked(False)
        gui._render_usage_summary(panel)
        self.assertTrue(graph.isHidden())
        self.assertTrue(details.isHidden())
        self.assertTrue(scroll.isHidden())
        if artifact_dir:
            Path(artifact_dir, "timings.txt").write_text(
                f"100 collapsed updates: {collapsed:.6f}s\n"
                f"1000-turn expanded update: {expanded:.6f}s\n"
            )
