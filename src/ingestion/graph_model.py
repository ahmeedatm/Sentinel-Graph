"""
Phase 3: Graph Model — SystemGraph Class
==========================================

Ce module implémente la classe SystemGraph, qui est la représentation
centrale du comportement du système en temps réel. Elle utilise NetworkX
pour gérer les nœuds (processus, fichiers, sockets) et les arêtes
(relations entre entités).

Role: 
  - Accumuler les événements Tetragon en structure graphe
  - Fournir des snapshots exploitables par l'Analyste
  - Permettre des requêtes rapides (voisins, chemins, etc.)
  
Architecture:
  +-------------------+
  | SystemGraph       |
  +-------------------+
  | - graph: DiGraph  |  (Directed graph from NetworkX)
  | - processes: {}   |  (Cache PID -> nœud ID)
  | - files: {}       |  (Cache Path -> nœud ID)
  | - sockets: {}     |  (Cache IP:Port -> nœud ID)
  +-------------------+
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import uuid
import json

try:
    from .constants import (
        NODE_PROCESS, NODE_FILE, NODE_SOCKET,
        REL_SPAWNS, REL_CONNECTS_TO, REL_MODIFIES, REL_READS,
    )
except ImportError:
    from constants import (  # type: ignore[no-redef]
        NODE_PROCESS, NODE_FILE, NODE_SOCKET,
        REL_SPAWNS, REL_CONNECTS_TO, REL_MODIFIES, REL_READS,
    )


class SystemGraph:
    """Représentation en graphe du système en temps réel."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.processes: Dict[Tuple[int, int], str] = {}  # (pid, uid) -> node_id
        self.files: Dict[str, str] = {}                   # path -> node_id
        self.sockets: Dict[Tuple[str, int], str] = {}     # (ip, port) -> node_id
    
    def add_process(self, pid: int, ppid: Optional[int], comm: str, 
                   uid: int, gid: int, pod_name: Optional[str] = None,
                   namespace: Optional[str] = None) -> str:
        node_key = (pid, uid)
        node_id = f"proc_{pid}_{uid}_{uuid.uuid4().hex[:8]}"
        
        if node_key in self.processes:
            node_id = self.processes[node_key]
        else:
            self.processes[node_key] = node_id
        
        self.graph.add_node(
            node_id,
            node_type=NODE_PROCESS,
            pid=pid,
            parent_pid=ppid,
            comm=comm,
            uid=uid,
            gid=gid,
            timestamp=datetime.now().isoformat(),
            pod_name=pod_name,
            namespace=namespace,
        )
        return node_id
    
    def _find_process_by_pid(self, pid: int) -> Optional[str]:
        for (p, _), node_id in self.processes.items():
            if p == pid:
                return node_id
        return None

    def add_process_spawn(self, parent_pid: int, child_pid: int, comm: str,
                         uid: int, gid: int,
                         pod_name: Optional[str] = None,
                         namespace: Optional[str] = None) -> Tuple[str, str]:
        existing_parent = self._find_process_by_pid(parent_pid)
        if existing_parent:
            parent_id = existing_parent
        else:
            parent_id = self.add_process(parent_pid, None, "<unknown_parent>", uid, gid,
                                         pod_name, namespace)
        
        child_id = self.add_process(child_pid, parent_pid, comm, uid, gid,
                                    pod_name, namespace)
        
        self.graph.add_edge(
            parent_id, child_id,
            relation=REL_SPAWNS,
            timestamp=datetime.now().isoformat(),
            count=1,
        )
        return parent_id, child_id
    
    def remove_process(self, pid: int, uid: int) -> bool:
        node_key = (pid, uid)
        if node_key in self.processes:
            node_id = self.processes[node_key]
            self.graph.remove_node(node_id)
            del self.processes[node_key]
            return True
        return False
    
    def add_file(self, path: str, mode: Optional[int] = None, 
                 size: Optional[int] = None, inode: Optional[int] = None) -> str:
        if path in self.files:
            return self.files[path]
        
        node_id = f"file_{uuid.uuid4().hex[:12]}"
        self.files[path] = node_id
        attrs = {
            "node_type": NODE_FILE,
            "path": path,
            "timestamp": datetime.now().isoformat(),
        }
        if mode is not None: attrs["mode"] = mode
        if size is not None: attrs["size"] = size
        if inode is not None: attrs["inode"] = inode
        
        self.graph.add_node(node_id, **attrs)
        return node_id
    
    def _ensure_process_exists(self, pid: int, uid: int) -> str:
        """Crée un processus fantôme s'il n'existe pas, pour éviter de perdre des événements tcp/file sans parent."""
        node_key = (pid, uid)
        if node_key not in self.processes:
            return self.add_process(pid, None, f"<unknown_pid_{pid}>", uid, 0)
        return self.processes[node_key]

    def add_file_access(self, pid: int, uid: int, path: str, 
                       access_type: str = "READ") -> Optional[Tuple[str, str]]:
        proc_id = self._ensure_process_exists(pid, uid)
        file_id = self.add_file(path)
        relation_type = REL_READS if access_type == "READ" else REL_MODIFIES
        
        if self.graph.has_edge(proc_id, file_id):
            self.graph[proc_id][file_id]["count"] = self.graph[proc_id][file_id].get("count", 1) + 1
            self.graph[proc_id][file_id]["last_seen"] = datetime.now().isoformat()
            if relation_type == REL_MODIFIES:
                self.graph[proc_id][file_id]["relation"] = REL_MODIFIES
        else:
            self.graph.add_edge(proc_id, file_id, relation=relation_type, timestamp=datetime.now().isoformat(), count=1)
        return proc_id, file_id
    
    def add_file_read(self, pid: int, uid: int, path: str) -> Optional[Tuple[str, str]]:
        return self.add_file_access(pid, uid, path, access_type="READ")
    
    def add_file_write(self, pid: int, uid: int, path: str) -> Optional[Tuple[str, str]]:
        return self.add_file_access(pid, uid, path, access_type="WRITE")
    
    def add_socket(self, ip: str, port: int, protocol: str = "TCP") -> str:
        socket_key = (ip, port)
        if socket_key in self.sockets:
            return self.sockets[socket_key]
        
        node_id = f"socket_{uuid.uuid4().hex[:12]}"
        self.sockets[socket_key] = node_id
        
        self.graph.add_node(node_id, node_type=NODE_SOCKET, ip=ip, port=port, protocol=protocol, timestamp=datetime.now().isoformat())
        return node_id
    
    def add_socket_connection(self, pid: int, uid: int, ip: str, port: int, protocol: str = "TCP") -> Optional[Tuple[str, str]]:
        proc_id = self._ensure_process_exists(pid, uid)
        socket_id = self.add_socket(ip, port, protocol)
        
        if self.graph.has_edge(proc_id, socket_id):
            self.graph[proc_id][socket_id]["count"] = self.graph[proc_id][socket_id].get("count", 1) + 1
            self.graph[proc_id][socket_id]["last_seen"] = datetime.now().isoformat()
        else:
            self.graph.add_edge(proc_id, socket_id, relation=REL_CONNECTS_TO, timestamp=datetime.now().isoformat(), count=1)
        return proc_id, socket_id
    
    def get_process_neighbors(self, pid: int, uid: int) -> Dict[str, List[str]]:
        node_key = (pid, uid)
        if node_key not in self.processes:
            return {"children": [], "files": [], "sockets": []}
        
        proc_id = self.processes[node_key]
        result = {"children": [], "files": [], "sockets": []}
        
        for succ_id in self.graph.successors(proc_id):
            relation = self.graph[proc_id][succ_id].get("relation", "UNKNOWN")
            if relation == REL_SPAWNS:
                result["children"].append(succ_id)
            elif relation in (REL_MODIFIES, REL_READS):
                result["files"].append(succ_id)
            elif relation == REL_CONNECTS_TO:
                result["sockets"].append(succ_id)
        return result
    
    def get_graph_snapshot(self) -> Dict[str, Any]:
        nodes = []
        edges = []
        
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node_id, "type": attrs.get("node_type"), "attributes": {k: v for k, v in attrs.items() if k != "node_type"}})
        
        for source, target, attrs in self.graph.edges(data=True):
            edges.append({"source": source, "target": target, "relation": attrs.get("relation"), "attributes": {k: v for k, v in attrs.items() if k != "relation"}})
        
        stats = {
            "num_processes": sum(1 for n in self.graph.nodes(data=True) if n[1].get("node_type") == NODE_PROCESS),
            "num_files": sum(1 for n in self.graph.nodes(data=True) if n[1].get("node_type") == NODE_FILE),
            "num_sockets": sum(1 for n in self.graph.nodes(data=True) if n[1].get("node_type") == NODE_SOCKET),
            "num_edges": len(list(self.graph.edges())),
        }
        
        return {"timestamp": datetime.now().isoformat(), "nodes": nodes, "edges": edges, "statistics": stats}
    
    def _graph_without_none_attrs(self) -> nx.DiGraph:
        clean = nx.DiGraph()
        for node_id, data in self.graph.nodes(data=True):
            clean.add_node(node_id, **{k: v for k, v in data.items() if v is not None})
        for src, tgt, data in self.graph.edges(data=True):
            clean.add_edge(src, tgt, **{k: v for k, v in data.items() if v is not None})
        return clean

    def export_graph(self, format: str = "json") -> str:
        if format == "json":
            return json.dumps(self.get_graph_snapshot(), indent=2, default=str)
        elif format == "gexf":
            import io
            buf = io.BytesIO()
            nx.write_gexf(self._graph_without_none_attrs(), buf)
            return buf.getvalue().decode("utf-8")
        elif format == "graphml":
            import io
            buf = io.BytesIO()
            nx.write_graphml(self._graph_without_none_attrs(), buf)
            return buf.getvalue().decode("utf-8")
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    def print_summary(self):
        snapshot = self.get_graph_snapshot()
        stats = snapshot["statistics"]
        print(f"\n{'='*60}")
        print(f"SystemGraph Summary - {snapshot['timestamp']}")
        print(f"{'='*60}")
        print(f"  Processus: {stats['num_processes']}")
        print(f"  Fichiers:  {stats['num_files']}")
        print(f"  Sockets:   {stats['num_sockets']}")
        print(f"  Arêtes:    {stats['num_edges']}")
        print(f"{'='*60}\n")
