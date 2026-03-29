"""
Unit tests for tetragon_adapter.py

Teste la normalisation du format Tetragon (camelCase imbriqué)
vers le format interne plat attendu par dispatch_event().
"""

import pytest
from ingestion.tetragon_adapter import normalize


# ============================================================================
# process_exec
# ============================================================================

class TestNormalizeProcessExec:

    def _event(self, pid=123, parent_pid=1, binary="/bin/bash",
                uid=0, namespace="default", pod_name="web"):
        return {
            "processExec": {
                "process": {
                    "pid": pid,
                    "uid": uid,
                    "binary": binary,
                    "pod": {"namespace": namespace, "name": pod_name},
                },
                "parent": {"pid": parent_pid},
            }
        }

    def test_event_type(self):
        result = normalize(self._event())
        assert result["event_type"] == "process_exec"

    def test_pid_extracted(self):
        assert normalize(self._event(pid=999))["pid"] == 999

    def test_parent_pid_extracted(self):
        assert normalize(self._event(parent_pid=42))["parent_pid"] == 42

    def test_comm_is_basename(self):
        assert normalize(self._event(binary="/usr/bin/python3"))["comm"] == "python3"

    def test_comm_from_root_binary(self):
        assert normalize(self._event(binary="/bin/sh"))["comm"] == "sh"

    def test_uid_extracted(self):
        assert normalize(self._event(uid=1000))["uid"] == 1000

    def test_pod_name_extracted(self):
        assert normalize(self._event(pod_name="backend"))["pod_name"] == "backend"

    def test_namespace_extracted(self):
        assert normalize(self._event(namespace="kube-system"))["namespace"] == "kube-system"

    def test_gid_defaults_to_zero(self):
        assert normalize(self._event())["gid"] == 0

    def test_missing_pid_returns_none(self):
        event = {"processExec": {"process": {"uid": 0}, "parent": {"pid": 1}}}
        assert normalize(event) is None

    def test_missing_parent_pid_returns_none(self):
        event = {"processExec": {"process": {"pid": 1, "uid": 0}, "parent": {}}}
        assert normalize(event) is None

    def test_empty_pod_does_not_crash(self):
        event = {
            "processExec": {
                "process": {"pid": 1, "uid": 0, "binary": "/bin/ls"},
                "parent": {"pid": 0},
            }
        }
        result = normalize(event)
        assert result is not None
        assert result["pod_name"] is None
        assert result["namespace"] is None


# ============================================================================
# process_exit
# ============================================================================

class TestNormalizeProcessExit:

    def test_event_type(self):
        event = {"processExit": {"process": {"pid": 10, "uid": 0}}}
        assert normalize(event)["event_type"] == "process_exit"

    def test_pid_extracted(self):
        event = {"processExit": {"process": {"pid": 55, "uid": 0}}}
        assert normalize(event)["pid"] == 55

    def test_uid_extracted(self):
        event = {"processExit": {"process": {"pid": 55, "uid": 1000}}}
        assert normalize(event)["uid"] == 1000

    def test_missing_pid_returns_none(self):
        event = {"processExit": {"process": {"uid": 0}}}
        assert normalize(event) is None


# ============================================================================
# process_kprobe — tcp_connect
# ============================================================================

class TestNormalizeKprobeTCPConnect:

    def _event(self, function_name="tcp_connect", daddr="8.8.8.8",
                dport=443, proto="TCP", pid=100, uid=0):
        return {
            "processKprobe": {
                "process": {"pid": pid, "uid": uid},
                "functionName": function_name,
                "args": [
                    {"sockArg": {"saddr": "10.0.0.1", "daddr": daddr,
                                 "sport": 54321, "dport": dport, "proto": proto}}
                ],
            }
        }

    def test_event_type(self):
        assert normalize(self._event())["event_type"] == "tcp_connect"

    def test_destination_ip(self):
        assert normalize(self._event(daddr="1.2.3.4"))["destination_ip"] == "1.2.3.4"

    def test_destination_port(self):
        assert normalize(self._event(dport=80))["destination_port"] == 80

    def test_protocol(self):
        assert normalize(self._event(proto="UDP"))["protocol"] == "UDP"

    def test_pid_extracted(self):
        assert normalize(self._event(pid=777))["pid"] == 777

    def test_tcp_v4_connect_alias(self):
        event = self._event(function_name="tcp_v4_connect")
        assert normalize(event)["event_type"] == "tcp_connect"

    def test_tcp_v6_connect_alias(self):
        event = self._event(function_name="tcp_v6_connect")
        assert normalize(event)["event_type"] == "tcp_connect"

    def test_missing_sock_arg_returns_none(self):
        event = {
            "processKprobe": {
                "process": {"pid": 1, "uid": 0},
                "functionName": "tcp_connect",
                "args": [{"stringArg": "irrelevant"}],
            }
        }
        assert normalize(event) is None


# ============================================================================
# process_kprobe — accès fichier
# ============================================================================

class TestNormalizeKprobeFile:

    def _kprobe_event(self, function_name, path="/etc/passwd", pid=100, uid=0):
        return {
            "processKprobe": {
                "process": {"pid": pid, "uid": uid},
                "functionName": function_name,
                "args": [{"pathArg": {"path": path}}],
            }
        }

    def test_file_open_event_type(self):
        event = self._kprobe_event("security_file_open")
        assert normalize(event)["event_type"] == "file_open"

    def test_file_write_event_type(self):
        event = self._kprobe_event("vfs_write")
        assert normalize(event)["event_type"] == "file_write"

    def test_file_read_event_type(self):
        event = self._kprobe_event("vfs_read")
        assert normalize(event)["event_type"] == "file_read"

    def test_path_extracted(self):
        event = self._kprobe_event("vfs_read", path="/var/log/syslog")
        assert normalize(event)["path"] == "/var/log/syslog"

    def test_file_arg_path_also_works(self):
        event = {
            "processKprobe": {
                "process": {"pid": 1, "uid": 0},
                "functionName": "vfs_write",
                "args": [{"fileArg": {"path": "/tmp/out.txt", "flags": 0}}],
            }
        }
        result = normalize(event)
        assert result["path"] == "/tmp/out.txt"

    def test_open_with_write_flags(self):
        # O_WRONLY = 0o1
        event = {
            "processKprobe": {
                "process": {"pid": 1, "uid": 0},
                "functionName": "security_file_open",
                "args": [{"fileArg": {"path": "/tmp/x", "flags": 1}}],
            }
        }
        result = normalize(event)
        assert result["event_type"] == "file_open"
        assert result["access_type"] == "WRITE"

    def test_open_with_read_flags(self):
        # flags = 0 → O_RDONLY
        event = {
            "processKprobe": {
                "process": {"pid": 1, "uid": 0},
                "functionName": "security_file_open",
                "args": [{"fileArg": {"path": "/tmp/x", "flags": 0}}],
            }
        }
        assert normalize(event)["access_type"] == "READ"

    def test_unknown_function_returns_none(self):
        event = self._kprobe_event("do_something_unknown")
        assert normalize(event) is None


# ============================================================================
# Événements non supportés
# ============================================================================

class TestNormalizeUnsupported:

    def test_unknown_top_level_key_returns_none(self):
        assert normalize({"someFutureEvent": {}}) is None

    def test_process_tracepoint_returns_none(self):
        event = {"processTracepoint": {"process": {"pid": 1}, "subsys": "net"}}
        assert normalize(event) is None

    def test_empty_dict_returns_none(self):
        assert normalize({}) is None
