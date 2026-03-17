"""
Unit tests for SystemGraph (graph_model.py).
"""

import json
import pytest
from ingestion import SystemGraph
from ingestion.constants import (
    NODE_PROCESS, NODE_FILE, NODE_SOCKET,
    REL_SPAWNS, REL_MODIFIES, REL_READS, REL_CONNECTS_TO,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sg():
    return SystemGraph()


@pytest.fixture
def sg_with_process(sg):
    """Graph with a single process (pid=100, uid=1000)."""
    sg.add_process(100, 1, "bash", 1000, 1000, "my-pod", "default")
    return sg


@pytest.fixture
def sg_with_spawn(sg):
    """Graph with parent (pid=1, uid=0) → child (pid=100, uid=1000)."""
    sg.add_process(1, None, "init", 0, 0)
    sg.add_process_spawn(1, 100, "bash", 1000, 1000, "my-pod", "default")
    return sg


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_init_empty_graph(sg):
    assert sg.graph.number_of_nodes() == 0
    assert sg.graph.number_of_edges() == 0
    assert sg.processes == {}
    assert sg.files == {}
    assert sg.sockets == {}


# ---------------------------------------------------------------------------
# add_process
# ---------------------------------------------------------------------------

def test_add_process_creates_node(sg):
    node_id = sg.add_process(100, 1, "bash", 1000, 1000)
    assert node_id in sg.graph.nodes
    attrs = sg.graph.nodes[node_id]
    assert attrs["node_type"] == NODE_PROCESS
    assert attrs["pid"] == 100
    assert attrs["comm"] == "bash"
    assert attrs["uid"] == 1000


def test_add_process_registers_in_cache(sg):
    sg.add_process(100, 1, "bash", 1000, 1000)
    assert (100, 1000) in sg.processes


def test_add_process_returns_same_id_on_duplicate(sg):
    id1 = sg.add_process(100, 1, "bash", 1000, 1000)
    id2 = sg.add_process(100, 1, "bash-updated", 1000, 1000)
    assert id1 == id2


def test_add_process_stores_kubernetes_context(sg):
    node_id = sg.add_process(100, 1, "nginx", 0, 0, "nginx-pod", "production")
    attrs = sg.graph.nodes[node_id]
    assert attrs["pod_name"] == "nginx-pod"
    assert attrs["namespace"] == "production"


# ---------------------------------------------------------------------------
# add_process_spawn
# ---------------------------------------------------------------------------

def test_add_process_spawn_creates_two_nodes(sg):
    sg.add_process_spawn(1, 100, "bash", 1000, 1000)
    assert sg.graph.number_of_nodes() == 2


def test_add_process_spawn_creates_spawns_edge(sg):
    parent_id, child_id = sg.add_process_spawn(1, 100, "bash", 1000, 1000)
    assert sg.graph.has_edge(parent_id, child_id)
    assert sg.graph[parent_id][child_id]["relation"] == REL_SPAWNS


def test_add_process_spawn_child_has_correct_comm(sg):
    _, child_id = sg.add_process_spawn(1, 100, "bash", 1000, 1000)
    assert sg.graph.nodes[child_id]["comm"] == "bash"


def test_add_process_spawn_reuses_existing_parent(sg):
    """Bug 1 fix: parent already in graph must not be duplicated or rekeyed."""
    sg.add_process(1, None, "init", 0, 0)
    node_count_before = sg.graph.number_of_nodes()
    sg.add_process_spawn(1, 100, "bash", 1000, 1000)
    # Parent node must not be duplicated
    assert sg.graph.number_of_nodes() == node_count_before + 1

def test_add_process_spawn_preserves_existing_parent_attributes(sg):
    """Bug 1 fix: existing parent comm/uid must not be overwritten by phantom."""
    sg.add_process(1, None, "init", 0, 0)
    parent_id = sg.processes[(1, 0)]
    sg.add_process_spawn(1, 100, "bash", 1000, 1000)
    # Parent node attributes must be unchanged
    assert sg.graph.nodes[parent_id]["comm"] == "init"
    assert sg.graph.nodes[parent_id]["uid"] == 0


def test_add_process_spawn_phantom_parent_not_keyed_with_child_uid(sg):
    """Bug 1 fix: when parent is unknown, phantom must not collide with child uid."""
    sg.add_process_spawn(1, 100, "bash", 1000, 1000)
    # The parent PID 1 must be findable
    assert sg._find_process_by_pid(1) is not None


# ---------------------------------------------------------------------------
# _find_process_by_pid
# ---------------------------------------------------------------------------

def test_find_process_by_pid_returns_node_id(sg_with_process):
    node_id = sg_with_process._find_process_by_pid(100)
    assert node_id is not None
    assert node_id == sg_with_process.processes[(100, 1000)]


def test_find_process_by_pid_returns_none_for_unknown(sg):
    assert sg._find_process_by_pid(999) is None


# ---------------------------------------------------------------------------
# remove_process
# ---------------------------------------------------------------------------

def test_remove_process_returns_true(sg_with_process):
    assert sg_with_process.remove_process(100, 1000) is True


def test_remove_process_deletes_node(sg_with_process):
    node_id = sg_with_process.processes[(100, 1000)]
    sg_with_process.remove_process(100, 1000)
    assert node_id not in sg_with_process.graph.nodes


def test_remove_process_clears_cache(sg_with_process):
    sg_with_process.remove_process(100, 1000)
    assert (100, 1000) not in sg_with_process.processes


def test_remove_process_unknown_pid_returns_false(sg):
    assert sg.remove_process(999, 0) is False


# ---------------------------------------------------------------------------
# add_file / add_file_access
# ---------------------------------------------------------------------------

def test_add_file_creates_node(sg):
    node_id = sg.add_file("/etc/passwd")
    assert node_id in sg.graph.nodes
    assert sg.graph.nodes[node_id]["node_type"] == NODE_FILE
    assert sg.graph.nodes[node_id]["path"] == "/etc/passwd"


def test_add_file_returns_same_id_for_duplicate_path(sg):
    id1 = sg.add_file("/etc/passwd")
    id2 = sg.add_file("/etc/passwd")
    assert id1 == id2


def test_add_file_access_read_creates_reads_edge(sg_with_spawn):
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "READ")
    proc_id = sg_with_spawn.processes[(100, 1000)]
    file_id = sg_with_spawn.files["/etc/passwd"]
    assert sg_with_spawn.graph[proc_id][file_id]["relation"] == REL_READS


def test_add_file_access_write_creates_modifies_edge(sg_with_spawn):
    sg_with_spawn.add_file_access(100, 1000, "/tmp/out.txt", "WRITE")
    proc_id = sg_with_spawn.processes[(100, 1000)]
    file_id = sg_with_spawn.files["/tmp/out.txt"]
    assert sg_with_spawn.graph[proc_id][file_id]["relation"] == REL_MODIFIES


def test_add_file_access_unknown_pid_returns_none(sg):
    result = sg.add_file_access(999, 0, "/etc/passwd")
    assert result is None


def test_add_file_access_increments_count(sg_with_spawn):
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "READ")
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "READ")
    proc_id = sg_with_spawn.processes[(100, 1000)]
    file_id = sg_with_spawn.files["/etc/passwd"]
    assert sg_with_spawn.graph[proc_id][file_id]["count"] == 2


def test_add_file_access_upgrades_relation_read_to_write(sg_with_spawn):
    """Bug 2 fix: READ followed by WRITE must upgrade edge relation to MODIFIES."""
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "READ")
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "WRITE")
    proc_id = sg_with_spawn.processes[(100, 1000)]
    file_id = sg_with_spawn.files["/etc/passwd"]
    assert sg_with_spawn.graph[proc_id][file_id]["relation"] == REL_MODIFIES


def test_add_file_access_write_not_downgraded_to_read(sg_with_spawn):
    """WRITE followed by READ must NOT downgrade to READS."""
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "WRITE")
    sg_with_spawn.add_file_access(100, 1000, "/etc/passwd", "READ")
    proc_id = sg_with_spawn.processes[(100, 1000)]
    file_id = sg_with_spawn.files["/etc/passwd"]
    assert sg_with_spawn.graph[proc_id][file_id]["relation"] == REL_MODIFIES


def test_add_file_read_shortcut(sg_with_spawn):
    result = sg_with_spawn.add_file_read(100, 1000, "/etc/resolv.conf")
    assert result is not None
    proc_id, file_id = result
    assert sg_with_spawn.graph[proc_id][file_id]["relation"] == REL_READS


def test_add_file_write_shortcut(sg_with_spawn):
    result = sg_with_spawn.add_file_write(100, 1000, "/tmp/out.txt")
    assert result is not None
    proc_id, file_id = result
    assert sg_with_spawn.graph[proc_id][file_id]["relation"] == REL_MODIFIES


# ---------------------------------------------------------------------------
# add_socket / add_socket_connection
# ---------------------------------------------------------------------------

def test_add_socket_creates_node(sg):
    node_id = sg.add_socket("8.8.8.8", 443, "TCP")
    assert node_id in sg.graph.nodes
    attrs = sg.graph.nodes[node_id]
    assert attrs["node_type"] == NODE_SOCKET
    assert attrs["ip"] == "8.8.8.8"
    assert attrs["port"] == 443


def test_add_socket_returns_same_id_for_duplicate(sg):
    id1 = sg.add_socket("8.8.8.8", 443)
    id2 = sg.add_socket("8.8.8.8", 443)
    assert id1 == id2


def test_add_socket_connection_creates_connects_to_edge(sg_with_spawn):
    sg_with_spawn.add_socket_connection(100, 1000, "8.8.8.8", 443)
    proc_id = sg_with_spawn.processes[(100, 1000)]
    socket_id = sg_with_spawn.sockets[("8.8.8.8", 443)]
    assert sg_with_spawn.graph[proc_id][socket_id]["relation"] == REL_CONNECTS_TO


def test_add_socket_connection_unknown_pid_returns_none(sg):
    result = sg.add_socket_connection(999, 0, "8.8.8.8", 443)
    assert result is None


def test_add_socket_connection_increments_count(sg_with_spawn):
    sg_with_spawn.add_socket_connection(100, 1000, "1.2.3.4", 80)
    sg_with_spawn.add_socket_connection(100, 1000, "1.2.3.4", 80)
    proc_id = sg_with_spawn.processes[(100, 1000)]
    socket_id = sg_with_spawn.sockets[("1.2.3.4", 80)]
    assert sg_with_spawn.graph[proc_id][socket_id]["count"] == 2


# ---------------------------------------------------------------------------
# get_process_neighbors
# ---------------------------------------------------------------------------

def test_get_process_neighbors_returns_children(sg_with_spawn):
    neighbors = sg_with_spawn.get_process_neighbors(1, 0)
    assert len(neighbors["children"]) == 1


def test_get_process_neighbors_returns_files(sg_with_spawn):
    sg_with_spawn.add_file_read(100, 1000, "/etc/passwd")
    # PID 1 spawned PID 100, so look up neighbors of PID 100
    neighbors = sg_with_spawn.get_process_neighbors(100, 1000)
    assert len(neighbors["files"]) == 1


def test_get_process_neighbors_returns_sockets(sg_with_spawn):
    sg_with_spawn.add_socket_connection(100, 1000, "8.8.8.8", 443)
    neighbors = sg_with_spawn.get_process_neighbors(100, 1000)
    assert len(neighbors["sockets"]) == 1


def test_get_process_neighbors_unknown_pid_returns_empty(sg):
    neighbors = sg.get_process_neighbors(999, 0)
    assert neighbors == {"children": [], "files": [], "sockets": []}


# ---------------------------------------------------------------------------
# get_graph_snapshot
# ---------------------------------------------------------------------------

def test_get_graph_snapshot_has_required_keys(sg_with_spawn):
    snapshot = sg_with_spawn.get_graph_snapshot()
    assert "timestamp" in snapshot
    assert "nodes" in snapshot
    assert "edges" in snapshot
    assert "statistics" in snapshot


def test_get_graph_snapshot_statistics(sg_with_spawn):
    sg_with_spawn.add_file_read(100, 1000, "/etc/passwd")
    sg_with_spawn.add_socket_connection(100, 1000, "8.8.8.8", 443)
    stats = sg_with_spawn.get_graph_snapshot()["statistics"]
    assert stats["num_processes"] == 2
    assert stats["num_files"] == 1
    assert stats["num_sockets"] == 1
    assert stats["num_edges"] == 3  # SPAWNS + READS + CONNECTS_TO


def test_get_graph_snapshot_node_structure(sg_with_spawn):
    snapshot = sg_with_spawn.get_graph_snapshot()
    for node in snapshot["nodes"]:
        assert "id" in node
        assert "type" in node
        assert "attributes" in node


def test_get_graph_snapshot_edge_structure(sg_with_spawn):
    snapshot = sg_with_spawn.get_graph_snapshot()
    for edge in snapshot["edges"]:
        assert "source" in edge
        assert "target" in edge
        assert "relation" in edge


# ---------------------------------------------------------------------------
# export_graph
# ---------------------------------------------------------------------------

def test_export_graph_json_is_valid(sg_with_spawn):
    output = sg_with_spawn.export_graph(format="json")
    data = json.loads(output)
    assert "nodes" in data
    assert "edges" in data


def test_export_graph_gexf_contains_xml(sg_with_spawn):
    output = sg_with_spawn.export_graph(format="gexf")
    assert "<?xml" in output or "<gexf" in output


def test_export_graph_graphml_contains_xml(sg_with_spawn):
    output = sg_with_spawn.export_graph(format="graphml")
    assert "<?xml" in output or "<graphml" in output


def test_export_graph_unsupported_format_raises(sg_with_spawn):
    with pytest.raises(ValueError):
        sg_with_spawn.export_graph(format="csv")


# ---------------------------------------------------------------------------
# print_summary (smoke test)
# ---------------------------------------------------------------------------

def test_print_summary_does_not_raise(sg_with_spawn, capsys):
    sg_with_spawn.print_summary()
    output = capsys.readouterr().out
    assert "Processus" in output
