"""
Baseline Learner — Build behavioral profiles from graph snapshots.

For each process comm seen during the learning phase, tracks:
  - spawns:   child comm names
  - reads:    file paths read
  - writes:   file paths written
  - connects: "ip:port" strings for network connections

Profiles are persisted as JSON for restarts.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

try:
    from ingestion.constants import (
        NODE_PROCESS, NODE_FILE, NODE_SOCKET,
        REL_SPAWNS, REL_READS, REL_MODIFIES, REL_CONNECTS_TO,
    )
except ImportError:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "ingestion"))
    from constants import (  # type: ignore[no-redef]
        NODE_PROCESS, NODE_FILE, NODE_SOCKET,
        REL_SPAWNS, REL_READS, REL_MODIFIES, REL_CONNECTS_TO,
    )

# Default storage directory relative to this file
_DEFAULT_STORAGE = Path(__file__).parent / "storage"


class BaselineLearner:
    """
    Learns behavioral profiles from SystemGraph snapshots.

    Call learn() repeatedly during a baseline observation window,
    then save() to persist. Reload later with BaselineLearner.load().
    """

    def __init__(self) -> None:
        self._snapshot_count: int = 0
        self._created_at: str = datetime.now().isoformat()
        # behaviors[comm] = {"spawns": set, "reads": set, "writes": set, "connects": set}
        self._behaviors: Dict[str, Dict[str, Set[str]]] = {}

    # -------------------------------------------------------------------------
    # Learning
    # -------------------------------------------------------------------------

    def learn(self, snapshot: Dict[str, Any]) -> None:
        """
        Update the behavioral profile from a snapshot dict produced by
        SystemGraph.get_graph_snapshot().

        Processes every edge in snapshot["edges"] and resolves node attributes
        from snapshot["nodes"].
        """
        nodes = snapshot.get("nodes", [])
        edges = snapshot.get("edges", [])

        # Build a fast lookup: node_id -> node dict
        node_map: Dict[str, Dict[str, Any]] = {n["id"]: n for n in nodes}

        for edge in edges:
            src_id = edge.get("source")
            tgt_id = edge.get("target")
            relation = edge.get("relation")

            src_node = node_map.get(src_id)
            tgt_node = node_map.get(tgt_id)

            if src_node is None or tgt_node is None:
                continue
            if src_node.get("type") != NODE_PROCESS:
                continue

            comm: str = src_node.get("attributes", {}).get("comm", "unknown")
            self._ensure_behavior(comm)

            if relation == REL_SPAWNS:
                child_comm = tgt_node.get("attributes", {}).get("comm", "unknown")
                self._behaviors[comm]["spawns"].add(child_comm)

            elif relation == REL_READS:
                path = tgt_node.get("attributes", {}).get("path")
                if path:
                    self._behaviors[comm]["reads"].add(path)

            elif relation == REL_MODIFIES:
                path = tgt_node.get("attributes", {}).get("path")
                if path:
                    self._behaviors[comm]["writes"].add(path)

            elif relation == REL_CONNECTS_TO:
                attrs = tgt_node.get("attributes", {})
                ip = attrs.get("ip")
                port = attrs.get("port")
                if ip is not None and port is not None:
                    self._behaviors[comm]["connects"].add("{0}:{1}".format(ip, port))

        self._snapshot_count += 1

    def _ensure_behavior(self, comm: str) -> None:
        """Initialize behavior entry for comm if not present."""
        if comm not in self._behaviors:
            self._behaviors[comm] = {
                "spawns": set(),
                "reads": set(),
                "writes": set(),
                "connects": set(),
            }

    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Return True if at least one snapshot has been learned."""
        return self._snapshot_count >= 1

    def get_profile(self) -> Dict[str, Any]:
        """
        Return a JSON-serializable profile dict.
        All sets are serialized as sorted lists for deterministic output.
        """
        return {
            "created_at": self._created_at,
            "updated_at": datetime.now().isoformat(),
            "snapshot_count": self._snapshot_count,
            "behaviors": {
                comm: {
                    "spawns": sorted(data["spawns"]),
                    "reads": sorted(data["reads"]),
                    "writes": sorted(data["writes"]),
                    "connects": sorted(data["connects"]),
                }
                for comm, data in self._behaviors.items()
            },
        }

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def save(self, path: Optional[str] = None) -> None:
        """
        Persist the profile as JSON.

        Args:
            path: File path to write. Defaults to
                  $DATA_DIR/baseline.json or src/analysis/storage/baseline.json.
        """
        file_path = Path(path) if path else self._default_path()
        file_path.parent.mkdir(parents=True, exist_ok=True)

        profile = self.get_profile()
        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(profile, fh, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "BaselineLearner":
        """
        Load a previously saved profile from JSON.

        Args:
            path: File path to read. Defaults to the standard storage location.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        file_path = Path(path) if path else cls._default_path()

        if not file_path.exists():
            raise FileNotFoundError("Baseline profile not found: {0}".format(file_path))

        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        learner = cls()
        learner._created_at = data.get("created_at", datetime.now().isoformat())
        learner._snapshot_count = data.get("snapshot_count", 0)

        for comm, behavior in data.get("behaviors", {}).items():
            learner._behaviors[comm] = {
                "spawns": set(behavior.get("spawns", [])),
                "reads": set(behavior.get("reads", [])),
                "writes": set(behavior.get("writes", [])),
                "connects": set(behavior.get("connects", [])),
            }

        return learner

    @staticmethod
    def _default_path() -> Path:
        data_dir = os.environ.get("DATA_DIR")
        if data_dir:
            return Path(data_dir) / "baseline.json"
        return _DEFAULT_STORAGE / "baseline.json"
