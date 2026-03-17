"""
Unit tests for EventCollector (collector.py).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from ingestion import EventCollector, SystemGraph
from ingestion.constants import REL_SPAWNS, REL_READS, REL_MODIFIES, REL_CONNECTS_TO


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def collector():
    return EventCollector()


@pytest.fixture
def json_file(tmp_path):
    """Factory that writes a JSON array to a temp file and returns its path."""
    def _make(events: list) -> str:
        p = tmp_path / "events.json"
        p.write_text(json.dumps(events))
        return str(p)
    return _make


@pytest.fixture
def ndjson_file(tmp_path):
    """Factory that writes newline-delimited JSON to a temp file."""
    def _make(events: list) -> str:
        p = tmp_path / "events.ndjson"
        p.write_text("\n".join(json.dumps(e) for e in events))
        return str(p)
    return _make


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_collector_creates_new_graph_by_default():
    c = EventCollector()
    assert isinstance(c.graph, SystemGraph)


def test_collector_accepts_existing_graph():
    sg = SystemGraph()
    c = EventCollector(graph=sg)
    assert c.graph is sg


def test_collector_initial_counts():
    c = EventCollector()
    assert c.event_count == 0
    assert c.error_count == 0


# ---------------------------------------------------------------------------
# parse_event
# ---------------------------------------------------------------------------

def test_parse_event_valid_json(collector):
    result = collector.parse_event('{"event_type": "process_exec", "pid": 1}')
    assert result == {"event_type": "process_exec", "pid": 1}


def test_parse_event_malformed_json_returns_none(collector):
    result = collector.parse_event("{not valid json")
    assert result is None


def test_parse_event_malformed_json_increments_error_count(collector):
    collector.parse_event("{not valid")
    assert collector.error_count == 1


def test_parse_event_non_dict_returns_none(collector):
    result = collector.parse_event("[1, 2, 3]")
    assert result is None


def test_parse_event_non_dict_does_not_increment_error_count(collector):
    collector.parse_event("[1, 2, 3]")
    assert collector.error_count == 0


# ---------------------------------------------------------------------------
# dispatch_event — routing
# ---------------------------------------------------------------------------

def test_dispatch_routes_process_exec(collector):
    with patch.object(collector, "_handle_process_exec", return_value=True) as mock:
        collector.dispatch_event({"event_type": "process_exec"})
        mock.assert_called_once()


def test_dispatch_routes_process_exit(collector):
    with patch.object(collector, "_handle_process_exit", return_value=True) as mock:
        collector.dispatch_event({"event_type": "process_exit"})
        mock.assert_called_once()


def test_dispatch_routes_tcp_connect(collector):
    with patch.object(collector, "_handle_tcp_connect", return_value=True) as mock:
        collector.dispatch_event({"event_type": "tcp_connect"})
        mock.assert_called_once()


def test_dispatch_routes_file_open(collector):
    with patch.object(collector, "_handle_file_open", return_value=True) as mock:
        collector.dispatch_event({"event_type": "file_open"})
        mock.assert_called_once()


def test_dispatch_routes_file_write(collector):
    with patch.object(collector, "_handle_file_write", return_value=True) as mock:
        collector.dispatch_event({"event_type": "file_write"})
        mock.assert_called_once()


def test_dispatch_routes_file_read(collector):
    with patch.object(collector, "_handle_file_read", return_value=True) as mock:
        collector.dispatch_event({"event_type": "file_read"})
        mock.assert_called_once()


def test_dispatch_unknown_event_type_returns_false(collector):
    result = collector.dispatch_event({"event_type": "unknown_syscall"})
    assert result is False


# ---------------------------------------------------------------------------
# _handle_process_exec
# ---------------------------------------------------------------------------

def test_handle_process_exec_success(collector):
    event = {"event_type": "process_exec", "pid": 100, "parent_pid": 1,
             "comm": "bash", "uid": 1000, "gid": 1000}
    result = collector._handle_process_exec(event)
    assert result is True
    assert (100, 1000) in collector.graph.processes


def test_handle_process_exec_missing_pid_returns_false(collector):
    event = {"event_type": "process_exec", "parent_pid": 1, "comm": "bash", "uid": 0, "gid": 0}
    assert collector._handle_process_exec(event) is False


def test_handle_process_exec_missing_parent_pid_returns_false(collector):
    event = {"event_type": "process_exec", "pid": 100, "comm": "bash", "uid": 0, "gid": 0}
    assert collector._handle_process_exec(event) is False


def test_handle_process_exec_uses_defaults_for_optional_fields(collector):
    event = {"event_type": "process_exec", "pid": 100, "parent_pid": 1, "comm": "bash"}
    result = collector._handle_process_exec(event)
    assert result is True  # uid/gid default to 0


# ---------------------------------------------------------------------------
# _handle_process_exit
# ---------------------------------------------------------------------------

def test_handle_process_exit_success(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "bash", "uid": 0, "gid": 0})
    result = collector._handle_process_exit({"pid": 100, "uid": 0})
    assert result is True
    assert (100, 0) not in collector.graph.processes


def test_handle_process_exit_missing_pid_returns_false(collector):
    assert collector._handle_process_exit({"uid": 0}) is False


# ---------------------------------------------------------------------------
# _handle_tcp_connect
# ---------------------------------------------------------------------------

def test_handle_tcp_connect_success(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "curl", "uid": 0, "gid": 0})
    event = {"pid": 100, "uid": 0, "destination_ip": "8.8.8.8", "destination_port": 443}
    assert collector._handle_tcp_connect(event) is True


def test_handle_tcp_connect_missing_ip_returns_false(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "curl", "uid": 0, "gid": 0})
    assert collector._handle_tcp_connect({"pid": 100, "uid": 0, "destination_port": 443}) is False


def test_handle_tcp_connect_missing_port_returns_false(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "curl", "uid": 0, "gid": 0})
    assert collector._handle_tcp_connect({"pid": 100, "uid": 0, "destination_ip": "8.8.8.8"}) is False


def test_handle_tcp_connect_missing_pid_returns_false(collector):
    assert collector._handle_tcp_connect({"destination_ip": "8.8.8.8", "destination_port": 443}) is False


# ---------------------------------------------------------------------------
# _handle_file_open / write / read
# ---------------------------------------------------------------------------

def test_handle_file_open_success(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "cat", "uid": 0, "gid": 0})
    assert collector._handle_file_open({"pid": 100, "uid": 0, "path": "/etc/passwd"}) is True


def test_handle_file_open_missing_path_returns_false(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "cat", "uid": 0, "gid": 0})
    assert collector._handle_file_open({"pid": 100, "uid": 0}) is False


def test_handle_file_write_success(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "bash", "uid": 0, "gid": 0})
    assert collector._handle_file_write({"pid": 100, "uid": 0, "path": "/tmp/out.txt"}) is True


def test_handle_file_write_missing_pid_returns_false(collector):
    assert collector._handle_file_write({"uid": 0, "path": "/tmp/out.txt"}) is False


def test_handle_file_read_success(collector):
    collector._handle_process_exec({"pid": 100, "parent_pid": 1, "comm": "bash", "uid": 0, "gid": 0})
    assert collector._handle_file_read({"pid": 100, "uid": 0, "path": "/etc/hosts"}) is True


def test_handle_file_read_missing_path_returns_false(collector):
    assert collector._handle_file_read({"pid": 100, "uid": 0}) is False


# ---------------------------------------------------------------------------
# process_json_file
# ---------------------------------------------------------------------------

SAMPLE_EVENTS = [
    {"event_type": "process_exec", "pid": 100, "parent_pid": 1,
     "comm": "bash", "uid": 0, "gid": 0},
    {"event_type": "file_read", "pid": 100, "uid": 0, "path": "/etc/passwd"},
    {"event_type": "tcp_connect", "pid": 100, "uid": 0,
     "destination_ip": "1.2.3.4", "destination_port": 80},
]


def test_process_json_file_array_format(json_file):
    path = json_file(SAMPLE_EVENTS)
    c = EventCollector()
    count = c.process_json_file(path)
    assert count == 3
    assert c.error_count == 0


def test_process_json_file_ndjson_format(ndjson_file):
    path = ndjson_file(SAMPLE_EVENTS)
    c = EventCollector()
    count = c.process_json_file(path)
    assert count == 3
    assert c.error_count == 0


def test_process_json_file_not_found_returns_zero(collector):
    result = collector.process_json_file("/nonexistent/path/file.json")
    assert result == 0


def test_process_json_file_invalid_json_returns_zero(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[{invalid json")
    c = EventCollector()
    result = c.process_json_file(str(bad))
    assert result == 0


def test_process_json_file_empty_lines_are_skipped(ndjson_file):
    path = ndjson_file(SAMPLE_EVENTS[:1])
    # Manually inject blank lines
    p = Path(path)
    p.write_text("\n" + p.read_text() + "\n\n")
    c = EventCollector()
    count = c.process_json_file(path)
    assert count == 1


# ---------------------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------------------

def test_get_statistics_structure(collector):
    stats = collector.get_statistics()
    assert "events_processed" in stats
    assert "errors" in stats
    assert "graph_snapshot" in stats


def test_get_statistics_after_processing(json_file):
    path = json_file(SAMPLE_EVENTS)
    c = EventCollector()
    c.process_json_file(path)
    stats = c.get_statistics()
    assert stats["events_processed"] == 3
    assert stats["errors"] == 0


# ---------------------------------------------------------------------------
# process_stdin
# ---------------------------------------------------------------------------

def test_process_stdin_reads_events(monkeypatch):
    lines = [json.dumps(e) + "\n" for e in SAMPLE_EVENTS]
    monkeypatch.setattr("sys.stdin", iter(lines))
    c = EventCollector()
    count = c.process_stdin()
    assert count == 3
    assert c.error_count == 0


def test_process_stdin_skips_blank_lines(monkeypatch):
    lines = ["\n", json.dumps(SAMPLE_EVENTS[0]) + "\n", "\n"]
    monkeypatch.setattr("sys.stdin", iter(lines))
    c = EventCollector()
    count = c.process_stdin()
    assert count == 1
