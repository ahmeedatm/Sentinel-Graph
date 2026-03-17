"""
Unit tests for AnomalyDetector and Alert (src/analysis/detector.py).
"""

import pytest

from analysis import BaselineLearner, AnomalyDetector, Alert
from analysis.detector import (
    ALERT_UNKNOWN_PROCESS,
    ALERT_UNEXPECTED_SPAWN,
    ALERT_UNEXPECTED_FILE_READ,
    ALERT_UNEXPECTED_FILE_WRITE,
    ALERT_UNEXPECTED_CONNECTION,
)


# ---------------------------------------------------------------------------
# Helpers — snapshot builders
# ---------------------------------------------------------------------------

def _node(node_id: str, node_type: str, **attrs) -> dict:
    return {"id": node_id, "type": node_type, "attributes": attrs}


def _edge(source: str, target: str, relation: str) -> dict:
    return {"source": source, "target": target, "relation": relation, "attributes": {}}


def _snapshot(nodes: list, edges: list) -> dict:
    return {"nodes": nodes, "edges": edges, "statistics": {}}


def _spawn_snap(parent_comm: str, child_comm: str) -> dict:
    p = _node("p1", "process", comm=parent_comm, pid=1, uid=0)
    c = _node("p2", "process", comm=child_comm, pid=2, uid=0)
    return _snapshot([p, c], [_edge("p1", "p2", "SPAWNS")])


def _read_snap(comm: str, path: str) -> dict:
    p = _node("p1", "process", comm=comm, pid=1, uid=0)
    f = _node("f1", "file", path=path)
    return _snapshot([p, f], [_edge("p1", "f1", "READS")])


def _write_snap(comm: str, path: str) -> dict:
    p = _node("p1", "process", comm=comm, pid=1, uid=0)
    f = _node("f1", "file", path=path)
    return _snapshot([p, f], [_edge("p1", "f1", "MODIFIES")])


def _connect_snap(comm: str, ip: str, port: int) -> dict:
    p = _node("p1", "process", comm=comm, pid=1, uid=0)
    s = _node("s1", "socket", ip=ip, port=port)
    return _snapshot([p, s], [_edge("p1", "s1", "CONNECTS_TO")])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_learner() -> BaselineLearner:
    return BaselineLearner()


@pytest.fixture
def bash_learner() -> BaselineLearner:
    """Baseline: bash spawns curl, reads /etc/resolv.conf, writes /tmp/out.txt,
    connects to 8.8.8.8:443."""
    learner = BaselineLearner()
    p_bash = _node("p1", "process", comm="bash", pid=1, uid=0)
    p_curl = _node("p2", "process", comm="curl", pid=2, uid=0)
    f_read = _node("fr", "file", path="/etc/resolv.conf")
    f_write = _node("fw", "file", path="/tmp/out.txt")
    sock = _node("s1", "socket", ip="8.8.8.8", port=443)
    edges = [
        _edge("p1", "p2", "SPAWNS"),
        _edge("p1", "fr", "READS"),
        _edge("p1", "fw", "MODIFIES"),
        _edge("p1", "s1", "CONNECTS_TO"),
    ]
    learner.learn(_snapshot([p_bash, p_curl, f_read, f_write, sock], edges))
    return learner


# ---------------------------------------------------------------------------
# Tests — Unknown process
# ---------------------------------------------------------------------------

def test_unknown_process_triggers_alert(empty_learner):
    detector = AnomalyDetector(empty_learner)
    snap = _read_snap("bash", "/etc/resolv.conf")
    alerts = detector.detect(snap)
    assert len(alerts) == 1
    assert alerts[0].alert_type == ALERT_UNKNOWN_PROCESS
    assert alerts[0].process_comm == "bash"


def test_unknown_process_severity_is_medium(empty_learner):
    detector = AnomalyDetector(empty_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/passwd"))
    assert alerts[0].severity == "MEDIUM"


# ---------------------------------------------------------------------------
# Tests — Known process with known behavior → no alert
# ---------------------------------------------------------------------------

def test_known_spawn_no_alert(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_spawn_snap("bash", "curl"))
    assert alerts == []


def test_known_read_no_alert(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/resolv.conf"))
    assert alerts == []


def test_known_write_no_alert(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_write_snap("bash", "/tmp/out.txt"))
    assert alerts == []


def test_known_connection_no_alert(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_connect_snap("bash", "8.8.8.8", 443))
    assert alerts == []


# ---------------------------------------------------------------------------
# Tests — Unexpected behaviors
# ---------------------------------------------------------------------------

def test_unexpected_spawn_high_severity(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_spawn_snap("bash", "nc"))
    assert len(alerts) == 1
    assert alerts[0].alert_type == ALERT_UNEXPECTED_SPAWN
    assert alerts[0].severity == "HIGH"
    assert alerts[0].process_comm == "bash"


def test_unexpected_file_read_non_sensitive_medium(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/home/user/.bashrc"))
    assert len(alerts) == 1
    assert alerts[0].alert_type == ALERT_UNEXPECTED_FILE_READ
    assert alerts[0].severity == "MEDIUM"


def test_unexpected_file_read_sensitive_high(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/passwd"))
    assert len(alerts) == 1
    assert alerts[0].alert_type == ALERT_UNEXPECTED_FILE_READ
    assert alerts[0].severity == "HIGH"


def test_unexpected_file_read_shadow_high(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/shadow"))
    assert alerts[0].severity == "HIGH"


def test_unexpected_file_read_ssh_subpath_high(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/.ssh/id_rsa"))
    assert alerts[0].severity == "HIGH"


def test_unexpected_file_write_non_sensitive_medium(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_write_snap("bash", "/var/log/app.log"))
    assert len(alerts) == 1
    assert alerts[0].alert_type == ALERT_UNEXPECTED_FILE_WRITE
    assert alerts[0].severity == "MEDIUM"


def test_unexpected_file_write_sensitive_high(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_write_snap("bash", "/etc/crontab"))
    assert alerts[0].severity == "HIGH"


def test_unexpected_connection_high(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_connect_snap("bash", "10.0.0.1", 4444))
    assert len(alerts) == 1
    assert alerts[0].alert_type == ALERT_UNEXPECTED_CONNECTION
    assert alerts[0].severity == "HIGH"


# ---------------------------------------------------------------------------
# Tests — Alert accumulation and clear
# ---------------------------------------------------------------------------

def test_detect_returns_only_new_alerts(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts1 = detector.detect(_read_snap("bash", "/etc/passwd"))
    alerts2 = detector.detect(_read_snap("bash", "/etc/shadow"))
    # Each call returns only its own new alerts
    assert len(alerts1) == 1
    assert len(alerts2) == 1
    # But total accumulates
    assert len(detector.alerts) == 2


def test_clear_alerts_empties_accumulator(bash_learner):
    detector = AnomalyDetector(bash_learner)
    detector.detect(_read_snap("bash", "/etc/passwd"))
    assert len(detector.alerts) == 1
    detector.clear_alerts()
    assert detector.alerts == []


def test_alerts_accumulate_across_calls(bash_learner):
    detector = AnomalyDetector(bash_learner)
    detector.detect(_spawn_snap("bash", "nc"))
    detector.detect(_connect_snap("bash", "1.2.3.4", 80))
    assert len(detector.alerts) == 2


# ---------------------------------------------------------------------------
# Tests — Alert structure
# ---------------------------------------------------------------------------

def test_alert_has_id_and_timestamp(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/passwd"))
    a = alerts[0]
    assert isinstance(a.id, str) and len(a.id) == 32  # uuid4 hex = 32 chars
    assert "T" in a.timestamp  # ISO datetime contains 'T'


def test_alert_evidence_contains_edge_and_nodes(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/passwd"))
    ev = alerts[0].evidence
    assert "edge" in ev
    assert "source_node" in ev
    assert "target_node" in ev
    assert ev["source_node"]["attributes"]["comm"] == "bash"


def test_alert_is_dataclass_instance(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(_read_snap("bash", "/etc/passwd"))
    assert isinstance(alerts[0], Alert)


# ---------------------------------------------------------------------------
# Tests — Empty snapshot produces no alerts
# ---------------------------------------------------------------------------

def test_empty_snapshot_no_alerts(bash_learner):
    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect({"nodes": [], "edges": [], "statistics": {}})
    assert alerts == []


# ---------------------------------------------------------------------------
# Tests — Non-process source nodes in snapshot are ignored
# ---------------------------------------------------------------------------

def test_file_source_ignored(bash_learner):
    """An edge from a file node should produce no alerts."""
    detector = AnomalyDetector(bash_learner)
    snap = _snapshot(
        [
            _node("f1", "file", path="/etc/passwd"),
            _node("p1", "process", comm="bash", pid=1, uid=0),
        ],
        [_edge("f1", "p1", "READS")],
    )
    alerts = detector.detect(snap)
    assert alerts == []


# ---------------------------------------------------------------------------
# Tests — Multiple edges in same snapshot
# ---------------------------------------------------------------------------

def test_multiple_new_edges_produce_multiple_alerts(bash_learner):
    """bash reads two unknown files → two alerts."""
    p = _node("p1", "process", comm="bash", pid=1, uid=0)
    f1 = _node("f1", "file", path="/new/file1.txt")
    f2 = _node("f2", "file", path="/new/file2.txt")
    edges = [_edge("p1", "f1", "READS"), _edge("p1", "f2", "READS")]
    snap = _snapshot([p, f1, f2], edges)

    detector = AnomalyDetector(bash_learner)
    alerts = detector.detect(snap)
    assert len(alerts) == 2
    assert all(a.alert_type == ALERT_UNEXPECTED_FILE_READ for a in alerts)
