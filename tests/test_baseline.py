"""
Unit tests for BaselineLearner (src/analysis/baseline.py).
"""

import json
import pytest
from pathlib import Path

from analysis import BaselineLearner


# ---------------------------------------------------------------------------
# Helpers — build minimal snapshots that mimic SystemGraph.get_graph_snapshot()
# ---------------------------------------------------------------------------

def _node(node_id: str, node_type: str, **attrs) -> dict:
    return {"id": node_id, "type": node_type, "attributes": attrs}


def _edge(source: str, target: str, relation: str) -> dict:
    return {"source": source, "target": target, "relation": relation, "attributes": {}}


def _spawn_snapshot() -> dict:
    """bash (pid 1) spawns curl (pid 2)."""
    parent = _node("proc_1", "process", comm="bash", pid=1, uid=0)
    child = _node("proc_2", "process", comm="curl", pid=2, uid=0)
    edge = _edge("proc_1", "proc_2", "SPAWNS")
    return {"nodes": [parent, child], "edges": [edge], "statistics": {}}


def _file_read_snapshot() -> dict:
    """bash reads /etc/resolv.conf."""
    proc = _node("proc_1", "process", comm="bash", pid=1, uid=0)
    fnode = _node("file_1", "file", path="/etc/resolv.conf")
    edge = _edge("proc_1", "file_1", "READS")
    return {"nodes": [proc, fnode], "edges": [edge], "statistics": {}}


def _file_write_snapshot() -> dict:
    """bash writes /tmp/out.txt."""
    proc = _node("proc_1", "process", comm="bash", pid=1, uid=0)
    fnode = _node("file_1", "file", path="/tmp/out.txt")
    edge = _edge("proc_1", "file_1", "MODIFIES")
    return {"nodes": [proc, fnode], "edges": [edge], "statistics": {}}


def _connect_snapshot() -> dict:
    """bash connects to 8.8.8.8:443."""
    proc = _node("proc_1", "process", comm="bash", pid=1, uid=0)
    sock = _node("sock_1", "socket", ip="8.8.8.8", port=443)
    edge = _edge("proc_1", "sock_1", "CONNECTS_TO")
    return {"nodes": [proc, sock], "edges": [edge], "statistics": {}}


def _multi_snapshot() -> dict:
    """
    bash spawns curl, reads /etc/resolv.conf, writes /tmp/out.txt,
    connects to 8.8.8.8:443.
    """
    proc_bash = _node("proc_1", "process", comm="bash", pid=1, uid=0)
    proc_curl = _node("proc_2", "process", comm="curl", pid=2, uid=0)
    fread = _node("file_r", "file", path="/etc/resolv.conf")
    fwrite = _node("file_w", "file", path="/tmp/out.txt")
    sock = _node("sock_1", "socket", ip="8.8.8.8", port=443)
    edges = [
        _edge("proc_1", "proc_2", "SPAWNS"),
        _edge("proc_1", "file_r", "READS"),
        _edge("proc_1", "file_w", "MODIFIES"),
        _edge("proc_1", "sock_1", "CONNECTS_TO"),
    ]
    return {
        "nodes": [proc_bash, proc_curl, fread, fwrite, sock],
        "edges": edges,
        "statistics": {},
    }


# ---------------------------------------------------------------------------
# Tests — is_ready()
# ---------------------------------------------------------------------------

def test_empty_learner_not_ready():
    assert BaselineLearner().is_ready() is False


def test_is_ready_after_one_learn():
    learner = BaselineLearner()
    learner.learn(_spawn_snapshot())
    assert learner.is_ready() is True


# ---------------------------------------------------------------------------
# Tests — snapshot_count
# ---------------------------------------------------------------------------

def test_snapshot_count_increments():
    learner = BaselineLearner()
    learner.learn(_spawn_snapshot())
    assert learner.get_profile()["snapshot_count"] == 1
    learner.learn(_file_read_snapshot())
    assert learner.get_profile()["snapshot_count"] == 2


# ---------------------------------------------------------------------------
# Tests — learn() extracts correct behaviors
# ---------------------------------------------------------------------------

def test_learn_spawns():
    learner = BaselineLearner()
    learner.learn(_spawn_snapshot())
    behaviors = learner.get_profile()["behaviors"]
    assert "bash" in behaviors
    assert "curl" in behaviors["bash"]["spawns"]


def test_learn_file_read():
    learner = BaselineLearner()
    learner.learn(_file_read_snapshot())
    behaviors = learner.get_profile()["behaviors"]
    assert "/etc/resolv.conf" in behaviors["bash"]["reads"]
    assert behaviors["bash"]["writes"] == []


def test_learn_file_write():
    learner = BaselineLearner()
    learner.learn(_file_write_snapshot())
    behaviors = learner.get_profile()["behaviors"]
    assert "/tmp/out.txt" in behaviors["bash"]["writes"]
    assert behaviors["bash"]["reads"] == []


def test_learn_socket_connection():
    learner = BaselineLearner()
    learner.learn(_connect_snapshot())
    behaviors = learner.get_profile()["behaviors"]
    assert "8.8.8.8:443" in behaviors["bash"]["connects"]


def test_learn_all_behaviors_in_one_snapshot():
    learner = BaselineLearner()
    learner.learn(_multi_snapshot())
    b = learner.get_profile()["behaviors"]["bash"]
    assert "curl" in b["spawns"]
    assert "/etc/resolv.conf" in b["reads"]
    assert "/tmp/out.txt" in b["writes"]
    assert "8.8.8.8:443" in b["connects"]


# ---------------------------------------------------------------------------
# Tests — multiple learn() calls accumulate (union semantics)
# ---------------------------------------------------------------------------

def test_multiple_learn_accumulates():
    learner = BaselineLearner()
    learner.learn(_file_read_snapshot())   # bash reads /etc/resolv.conf
    learner.learn(_file_write_snapshot())  # bash writes /tmp/out.txt
    b = learner.get_profile()["behaviors"]["bash"]
    assert "/etc/resolv.conf" in b["reads"]
    assert "/tmp/out.txt" in b["writes"]


def test_multiple_learn_deduplicates():
    """Learning the same snapshot twice should not duplicate entries."""
    learner = BaselineLearner()
    learner.learn(_file_read_snapshot())
    learner.learn(_file_read_snapshot())
    b = learner.get_profile()["behaviors"]["bash"]
    assert b["reads"].count("/etc/resolv.conf") == 1


# ---------------------------------------------------------------------------
# Tests — profile serializes as sorted lists
# ---------------------------------------------------------------------------

def test_profile_sorted_lists():
    learner = BaselineLearner()
    # Learn two snapshots that add paths in reverse alphabetical order
    snap1 = {
        "nodes": [
            _node("p1", "process", comm="bash", pid=1, uid=0),
            _node("f1", "file", path="/z_file"),
        ],
        "edges": [_edge("p1", "f1", "READS")],
        "statistics": {},
    }
    snap2 = {
        "nodes": [
            _node("p1", "process", comm="bash", pid=1, uid=0),
            _node("f2", "file", path="/a_file"),
        ],
        "edges": [_edge("p1", "f2", "READS")],
        "statistics": {},
    }
    learner.learn(snap1)
    learner.learn(snap2)
    reads = learner.get_profile()["behaviors"]["bash"]["reads"]
    assert reads == sorted(reads)


# ---------------------------------------------------------------------------
# Tests — save() / load() round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    learner = BaselineLearner()
    learner.learn(_multi_snapshot())

    save_path = str(tmp_path / "baseline.json")
    learner.save(save_path)

    loaded = BaselineLearner.load(save_path)

    assert loaded.is_ready() is True
    assert loaded.get_profile()["snapshot_count"] == 1

    orig = learner.get_profile()["behaviors"]
    restored = loaded.get_profile()["behaviors"]
    assert orig.keys() == restored.keys()
    for comm in orig:
        assert orig[comm]["spawns"] == restored[comm]["spawns"]
        assert orig[comm]["reads"] == restored[comm]["reads"]
        assert orig[comm]["writes"] == restored[comm]["writes"]
        assert orig[comm]["connects"] == restored[comm]["connects"]


def test_save_creates_parent_dirs(tmp_path):
    learner = BaselineLearner()
    learner.learn(_spawn_snapshot())
    deep_path = str(tmp_path / "a" / "b" / "c" / "profile.json")
    learner.save(deep_path)
    assert Path(deep_path).exists()


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        BaselineLearner.load("/non/existent/path/baseline.json")


# ---------------------------------------------------------------------------
# Tests — saved JSON is valid and human-readable
# ---------------------------------------------------------------------------

def test_saved_json_is_valid(tmp_path):
    learner = BaselineLearner()
    learner.learn(_multi_snapshot())
    path = tmp_path / "test.json"
    learner.save(str(path))

    with open(path) as fh:
        data = json.load(fh)

    assert "behaviors" in data
    assert "bash" in data["behaviors"]
    assert isinstance(data["behaviors"]["bash"]["spawns"], list)


# ---------------------------------------------------------------------------
# Tests — non-process source nodes are ignored
# ---------------------------------------------------------------------------

def test_non_process_source_ignored():
    """Edges where source is a file node must not create any behavior."""
    learner = BaselineLearner()
    snap = {
        "nodes": [
            _node("f1", "file", path="/etc/passwd"),
            _node("p1", "process", comm="bash", pid=1, uid=0),
        ],
        "edges": [_edge("f1", "p1", "READS")],
        "statistics": {},
    }
    learner.learn(snap)
    # No behaviors should be recorded for "file" type source
    behaviors = learner.get_profile()["behaviors"]
    assert "bash" not in behaviors
