"""
Tetragon Adapter
================

Traduit les événements au format natif Tetragon (gRPC/dict imbriqué)
vers le format interne plat attendu par EventCollector.dispatch_event().

Format Tetragon (dict après MessageToDict) :
    {
        "processExec": {
            "process": {"pid": 123, "uid": 0, "binary": "/bin/bash",
                        "pod": {"namespace": "default", "name": "web"}},
            "parent":  {"pid": 1, "binary": "/sbin/init"}
        },
        "nodeName": "worker-1"
    }

Format interne (attendu par dispatch_event) :
    {
        "event_type": "process_exec",
        "pid": 123, "parent_pid": 1,
        "comm": "bash", "uid": 0, "gid": 0,
        "pod_name": "web", "namespace": "default"
    }

Note : les clés Tetragon sont en camelCase (MessageToDict).
       Les clés internes sont en snake_case.
"""

import os
import logging
from typing import Dict, Any, Optional

try:
    from .constants import (
        EVENT_PROCESS_EXEC, EVENT_PROCESS_EXIT,
        EVENT_TCP_CONNECT, EVENT_FILE_OPEN, EVENT_FILE_WRITE, EVENT_FILE_READ,
    )
except ImportError:
    from constants import (  # type: ignore[no-redef]
        EVENT_PROCESS_EXEC, EVENT_PROCESS_EXIT,
        EVENT_TCP_CONNECT, EVENT_FILE_OPEN, EVENT_FILE_WRITE, EVENT_FILE_READ,
    )

logger = logging.getLogger(__name__)

# Noms de fonctions kernel associées aux connexions TCP
_TCP_FUNCTIONS = {"tcp_connect", "tcp_v4_connect", "tcp_v6_connect"}

# Noms de fonctions kernel associées aux accès fichier
_FILE_OPEN_FUNCTIONS = {"security_file_open", "vfs_open", "__do_sys_openat2"}
_FILE_WRITE_FUNCTIONS = {"vfs_write", "vfs_writev", "__kernel_write"}
_FILE_READ_FUNCTIONS = {"vfs_read", "vfs_readv"}


def normalize(tetragon_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Point d'entrée principal. Dispatche selon le type d'événement Tetragon.

    Args:
        tetragon_event: Dict produit par MessageToDict(GetEventsResponse)

    Returns:
        Événement au format interne, ou None si le type n'est pas supporté.
    """
    if "processExec" in tetragon_event:
        return _normalize_process_exec(tetragon_event)
    if "processExit" in tetragon_event:
        return _normalize_process_exit(tetragon_event)
    if "processKprobe" in tetragon_event:
        return _normalize_process_kprobe(tetragon_event)
    if "processTracepoint" in tetragon_event:
        return _normalize_process_tracepoint(tetragon_event)

    logger.debug("Type d'événement Tetragon non supporté: %s", list(tetragon_event.keys()))
    return None


# ============================================================================
# Normaliseurs par type
# ============================================================================

def _normalize_process_exec(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Tetragon processExec → format interne process_exec.

    Champs extraits:
        process.pid, process.uid, process.binary, process.pod
        parent.pid
    """
    exec_data = event.get("processExec", {})
    process = exec_data.get("process", {})
    parent = exec_data.get("parent", {})

    pid = _to_int(process.get("pid"))
    parent_pid = _to_int(parent.get("pid"))

    if pid is None or parent_pid is None:
        logger.warning("processExec: pid ou parent_pid manquant — %s", event)
        return None

    pod = process.get("pod", {})

    return {
        "event_type": EVENT_PROCESS_EXEC,
        "pid": pid,
        "parent_pid": parent_pid,
        "comm": _basename(process.get("binary", "unknown")),
        "uid": _to_int(process.get("uid"), default=0),
        "gid": 0,  # non exposé directement dans process_exec Tetragon
        "pod_name": pod.get("name"),
        "namespace": pod.get("namespace"),
    }


def _normalize_process_exit(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Tetragon processExit → format interne process_exit.
    """
    exit_data = event.get("processExit", {})
    process = exit_data.get("process", {})

    pid = _to_int(process.get("pid"))
    if pid is None:
        logger.warning("processExit: pid manquant — %s", event)
        return None

    return {
        "event_type": EVENT_PROCESS_EXIT,
        "pid": pid,
        "uid": _to_int(process.get("uid"), default=0),
    }


def _normalize_process_kprobe(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Tetragon processKprobe → format interne tcp_connect / file_*.

    La fonction kernel hookée détermine le type d'événement.
    """
    kprobe = event.get("processKprobe", {})
    function_name = kprobe.get("functionName", "")
    process = kprobe.get("process", {})
    args = kprobe.get("args", [])

    pid = _to_int(process.get("pid"))
    uid = _to_int(process.get("uid"), default=0)

    if pid is None:
        logger.warning("processKprobe: pid manquant — %s", event)
        return None

    if function_name in _TCP_FUNCTIONS:
        return _kprobe_to_tcp_connect(pid, uid, args)

    if function_name in _FILE_WRITE_FUNCTIONS:
        return _kprobe_to_file_event(pid, uid, args, EVENT_FILE_WRITE)

    if function_name in _FILE_READ_FUNCTIONS:
        return _kprobe_to_file_event(pid, uid, args, EVENT_FILE_READ)

    if function_name in _FILE_OPEN_FUNCTIONS:
        return _kprobe_to_file_open(pid, uid, args)

    logger.debug("processKprobe: fonction non gérée '%s'", function_name)
    return None


def _normalize_process_tracepoint(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Tetragon processTracepoint — actuellement non mappé, ignoré.
    """
    logger.debug("processTracepoint ignoré: %s", event.get("processTracepoint", {}).get("event"))
    return None


# ============================================================================
# Helpers kprobe → événements réseau / fichier
# ============================================================================

def _kprobe_to_tcp_connect(
    pid: int, uid: int, args: list
) -> Optional[Dict[str, Any]]:
    """Extrait l'argument SockArg et produit un tcp_connect."""
    sock = _find_sock_arg(args)
    if sock is None:
        logger.warning("tcp_connect: argument SockArg introuvable")
        return None

    daddr = sock.get("daddr", "")
    dport = _to_int(sock.get("dport"), default=0)
    protocol = sock.get("proto", "TCP")

    return {
        "event_type": EVENT_TCP_CONNECT,
        "pid": pid,
        "uid": uid,
        "destination_ip": daddr,
        "destination_port": dport,
        "protocol": protocol,
    }


def _kprobe_to_file_open(
    pid: int, uid: int, args: list
) -> Optional[Dict[str, Any]]:
    """Extrait le chemin fichier et produit un file_open."""
    path = _find_path_arg(args)
    if path is None:
        return None

    flags = _extract_flags(args)
    access_type = "WRITE" if flags and _flag_is_write(flags) else "READ"

    return {
        "event_type": EVENT_FILE_OPEN,
        "pid": pid,
        "uid": uid,
        "path": path,
        "access_type": access_type,
    }


def _kprobe_to_file_event(
    pid: int, uid: int, args: list, event_type: str
) -> Optional[Dict[str, Any]]:
    """Produit un file_write ou file_read à partir d'un kprobe vfs_write/vfs_read."""
    path = _find_path_arg(args)
    if path is None:
        return None

    return {
        "event_type": event_type,
        "pid": pid,
        "uid": uid,
        "path": path,
    }


# ============================================================================
# Utilitaires d'extraction d'arguments kprobe
# ============================================================================

def _find_sock_arg(args: list) -> Optional[Dict[str, Any]]:
    """Retourne le premier argument de type sockArg, ou None."""
    for arg in args:
        if "sockArg" in arg:
            return arg["sockArg"]
    return None


def _find_path_arg(args: list) -> Optional[str]:
    """Retourne le premier chemin trouvé (pathArg ou fileArg), ou None."""
    for arg in args:
        if "pathArg" in arg:
            return arg["pathArg"].get("path")
        if "fileArg" in arg:
            return arg["fileArg"].get("path")
    return None


def _extract_flags(args: list) -> Optional[int]:
    """Retourne les flags d'un fileArg, ou None."""
    for arg in args:
        if "fileArg" in arg:
            raw = arg["fileArg"].get("flags")
            return _to_int(raw)
    return None


def _flag_is_write(flags: int) -> bool:
    """Vérifie si les flags O_WRONLY ou O_RDWR sont présents."""
    O_WRONLY = 0o1
    O_RDWR = 0o2
    return bool(flags & (O_WRONLY | O_RDWR))


# ============================================================================
# Petits utilitaires
# ============================================================================

def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Convertit value en int, retourne default si impossible."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _basename(binary_path: str) -> str:
    """Extrait le nom de l'exécutable depuis son chemin."""
    return os.path.basename(binary_path) if binary_path else "unknown"
