"""
Integration tests: full pipeline from dummy_logs.json to graph snapshot.
"""

import json
from pathlib import Path

import pytest
from ingestion import EventCollector
from ingestion.constants import REL_SPAWNS, REL_READS, REL_MODIFIES, REL_CONNECTS_TO

DUMMY_LOGS = Path(__file__).parent.parent / "src" / "ingestion" / "dummy_logs.json"


@pytest.fixture(scope="module")
def processed_collector():
    """Run the full pipeline once and reuse across tests in this module."""
    c = EventCollector()
    c.process_json_file(str(DUMMY_LOGS))
    return c


# ---------------------------------------------------------------------------
# Basic pipeline checks
# ---------------------------------------------------------------------------

def test_dummy_logs_file_exists():
    assert DUMMY_LOGS.exists(), f"dummy_logs.json not found at {DUMMY_LOGS}"


def test_all_events_processed(processed_collector):
    assert processed_collector.event_count == 9


def test_zero_errors(processed_collector):
    assert processed_collector.error_count == 0


# ---------------------------------------------------------------------------
# Graph statistics
# ---------------------------------------------------------------------------

def test_graph_has_four_processes(processed_collector):
    stats = processed_collector.graph.get_graph_snapshot()["statistics"]
    assert stats["num_processes"] == 4


def test_graph_has_four_files(processed_collector):
    stats = processed_collector.graph.get_graph_snapshot()["statistics"]
    assert stats["num_files"] == 4


def test_graph_has_two_sockets(processed_collector):
    stats = processed_collector.graph.get_graph_snapshot()["statistics"]
    assert stats["num_sockets"] == 2


def test_graph_has_nine_edges(processed_collector):
    stats = processed_collector.graph.get_graph_snapshot()["statistics"]
    assert stats["num_edges"] == 9


# ---------------------------------------------------------------------------
# Expected nodes and edges from dummy_logs.json
# ---------------------------------------------------------------------------

def test_bash_process_exists(processed_collector):
    # bash is pid=100, uid=1000
    assert (100, 1000) in processed_collector.graph.processes


def test_curl_process_exists(processed_collector):
    assert (101, 1000) in processed_collector.graph.processes


def test_python3_process_exists(processed_collector):
    assert (102, 1000) in processed_collector.graph.processes


def test_google_dns_socket_exists(processed_collector):
    assert ("8.8.8.8", 443) in processed_collector.graph.sockets


def test_db_socket_exists(processed_collector):
    assert ("192.168.1.100", 5432) in processed_collector.graph.sockets


def test_etc_resolv_conf_file_exists(processed_collector):
    assert "/etc/resolv.conf" in processed_collector.graph.files


def test_app_log_file_exists(processed_collector):
    assert "/var/log/app.log" in processed_collector.graph.files


def test_spawn_chain_bash_to_curl(processed_collector):
    """bash (pid=100) must have spawned curl (pid=101)."""
    sg = processed_collector.graph
    bash_id = sg.processes[(100, 1000)]
    curl_id = sg.processes[(101, 1000)]
    assert sg.graph.has_edge(bash_id, curl_id)
    assert sg.graph[bash_id][curl_id]["relation"] == REL_SPAWNS


def test_spawn_chain_curl_to_python3(processed_collector):
    """curl (pid=101) must have spawned python3 (pid=102)."""
    sg = processed_collector.graph
    curl_id = sg.processes[(101, 1000)]
    py_id = sg.processes[(102, 1000)]
    assert sg.graph.has_edge(curl_id, py_id)


def test_curl_connects_to_google_dns(processed_collector):
    sg = processed_collector.graph
    curl_id = sg.processes[(101, 1000)]
    socket_id = sg.sockets[("8.8.8.8", 443)]
    assert sg.graph.has_edge(curl_id, socket_id)
    assert sg.graph[curl_id][socket_id]["relation"] == REL_CONNECTS_TO


def test_bash_reads_resolv_conf(processed_collector):
    sg = processed_collector.graph
    bash_id = sg.processes[(100, 1000)]
    file_id = sg.files["/etc/resolv.conf"]
    assert sg.graph.has_edge(bash_id, file_id)
    assert sg.graph[bash_id][file_id]["relation"] == REL_READS


def test_python3_writes_app_log(processed_collector):
    sg = processed_collector.graph
    py_id = sg.processes[(102, 1000)]
    file_id = sg.files["/var/log/app.log"]
    assert sg.graph.has_edge(py_id, file_id)
    assert sg.graph[py_id][file_id]["relation"] == REL_MODIFIES


# ---------------------------------------------------------------------------
# Snapshot contract for L'Analyste
# ---------------------------------------------------------------------------

def test_snapshot_is_json_serialisable(processed_collector):
    snapshot = processed_collector.graph.get_graph_snapshot()
    # Must not raise
    serialised = json.dumps(snapshot, default=str)
    data = json.loads(serialised)
    assert data["statistics"]["num_processes"] == 4


def test_snapshot_nodes_have_types(processed_collector):
    snapshot = processed_collector.graph.get_graph_snapshot()
    types = {n["type"] for n in snapshot["nodes"]}
    assert "process" in types
    assert "file" in types
    assert "socket" in types


def test_snapshot_edges_have_relations(processed_collector):
    snapshot = processed_collector.graph.get_graph_snapshot()
    relations = {e["relation"] for e in snapshot["edges"]}
    assert REL_SPAWNS in relations
    assert REL_READS in relations
    assert REL_CONNECTS_TO in relations


# ---------------------------------------------------------------------------
# Export formats
# ---------------------------------------------------------------------------

def test_export_json_round_trip(processed_collector):
    output = processed_collector.graph.export_graph(format="json")
    data = json.loads(output)
    assert len(data["nodes"]) == 10  # 4 processes + 4 files + 2 sockets


def test_export_gexf_is_xml(processed_collector):
    output = processed_collector.graph.export_graph(format="gexf")
    assert "<?xml" in output or "<gexf" in output


def test_export_graphml_is_xml(processed_collector):
    output = processed_collector.graph.export_graph(format="graphml")
    assert "<?xml" in output or "<graphml" in output
