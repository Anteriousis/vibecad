# SPDX-License-Identifier: LGPL-2.1-or-later
"""Usage rendering must leave collapsed conversations idle."""
from types import SimpleNamespace

import pytest

import VibeCADGui as gui


@pytest.mark.parametrize("expanded", [False, True])
def test_usage_disclosure_scans_history_once_only_when_expanded(monkeypatch, expanded):
    scans = []
    graphs = []
    visible = {}
    output = SimpleNamespace(property=lambda name: None)
    details = SimpleNamespace(
        setText=lambda text: None,
        setVisible=lambda value: visible.update(details=value),
        setToolTip=lambda text: None,
    )
    toggle = SimpleNamespace(isChecked=lambda: expanded, setToolTip=lambda text: None)
    graph = SimpleNamespace(
        set_usage_data=graphs.append,
        setVisible=lambda value: visible.update(graph=value),
    )
    children = {"VibeConversation": output, "VibeUsageSummaryDetails": details,
                "VibeUsageSummaryToggle": toggle, "VibeUsageGraph": graph}
    monkeypatch.setattr(gui, "_find_child", lambda kind, name, dock: children.get(name))
    monkeypatch.setattr(gui, "_conversation_usage_entries", lambda widget: scans.append(widget) or [])
    gui._render_usage_summary()
    assert len(scans) == int(expanded)
    assert len(graphs) == int(expanded)
    assert visible == {"details": expanded, "graph": expanded}
