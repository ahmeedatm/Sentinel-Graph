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
      Methods:
      - add_process_spawn(parent_pid, child_pid, comm)
      - add_socket_connection(pid, ip, port, protocol)
      - add_file_access(pid, path, mode, access_type)
      - get_graph_snapshot()
      - export_graph()
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
    """
    Représentation en graphe du système en temps réel.
    
    Attributes:
        graph: DiGraph NetworkX (nœuds = entités, arêtes = relations)
        processes: Dictionnaire {(pid, uid): node_id} pour accès rapide
        files: Dictionnaire {path: node_id} pour accès rapide
        sockets: Dictionnaire {(ip, port): node_id} pour accès rapide
    """
    
    def __init__(self):
        """Initialise un graphe vide."""
        self.graph = nx.DiGraph()
        self.processes: Dict[Tuple[int, int], str] = {}  # (pid, uid) -> node_id
        self.files: Dict[str, str] = {}                   # path -> node_id
        self.sockets: Dict[Tuple[str, int], str] = {}     # (ip, port) -> node_id
    
    # ========================================================================
    # Gestion des Nœuds Processus
    # ========================================================================
    
    def add_process(self, pid: int, ppid: Optional[int], comm: str, 
                   uid: int, gid: int, pod_name: Optional[str] = None,
                   namespace: Optional[str] = None) -> str:
        """
        Ajoute ou met à jour un nœud processus.
        
        Args:
            pid: Process ID
            ppid: Parent Process ID (None si root)
            comm: Nom du processus (ex: "bash")
            uid: User ID
            gid: Group ID
            pod_name: Nom du pod K8s (optionnel)
            namespace: Namespace K8s (optionnel)
            
        Returns:
            node_id: Identifiant unique du nœud dans le graphe
        """
        node_key = (pid, uid)
        node_id = f"proc_{pid}_{uid}_{uuid.uuid4().hex[:8]}"
        
        # Si le processus existe déjà, on le met à jour
        if node_key in self.processes:
            node_id = self.processes[node_key]
        else:
            self.processes[node_key] = node_id
        
        # Ajouter/mettre à jour le nœud
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
        """
        Recherche un nœud processus par PID seul (ignore l'UID).
        Utilisé pour retrouver un parent existant lors d'un execve.

        Returns:
            node_id si trouvé, None sinon
        """
        for (p, _), node_id in self.processes.items():
            if p == pid:
                return node_id
        return None

    def add_process_spawn(self, parent_pid: int, child_pid: int, comm: str,
                         uid: int, gid: int,
                         pod_name: Optional[str] = None,
                         namespace: Optional[str] = None) -> Tuple[str, str]:
        """
        Enregistre le spawn d'un processus (execve event).
        Crée l'arête SPAWNS entre parent et enfant.

        Args:
            parent_pid: PID du processus parent
            child_pid: PID du processus enfant
            comm: Nom du processus enfant
            uid, gid: Propriétaire
            pod_name, namespace: Contexte K8s

        Returns:
            (parent_node_id, child_node_id)
        """
        # Chercher le parent par PID (indépendamment de l'UID),
        # car l'événement execve ne contient que l'UID de l'enfant.
        existing_parent = self._find_process_by_pid(parent_pid)
        if existing_parent:
            parent_id = existing_parent
        else:
            parent_id = self.add_process(parent_pid, None, "unknown", uid, gid,
                                         pod_name, namespace)
        
        # Ajouter l'enfant
        child_id = self.add_process(child_pid, parent_pid, comm, uid, gid,
                                    pod_name, namespace)
        
        # Créer l'arête SPAWNS
        self.graph.add_edge(
            parent_id, child_id,
            relation=REL_SPAWNS,
            timestamp=datetime.now().isoformat(),
            count=1,
        )
        
        return parent_id, child_id
    
    def remove_process(self, pid: int, uid: int) -> bool:
        """
        Supprime un processus (optionnel, pour cleanup futur).
        
        Returns:
            True si suppression effectuée, False si PID non trouvé
        """
        node_key = (pid, uid)
        if node_key in self.processes:
            node_id = self.processes[node_key]
            self.graph.remove_node(node_id)
            del self.processes[node_key]
            return True
        return False
    
    # ========================================================================
    # Gestion des Nœuds Fichier
    # ========================================================================
    
    def add_file(self, path: str, mode: Optional[int] = None, 
                 size: Optional[int] = None, inode: Optional[int] = None) -> str:
        """
        Ajoute ou récupère un nœud fichier.
        
        Args:
            path: Chemin complet du fichier
            mode, size, inode: Attributs optionnels
            
        Returns:
            node_id
        """
        if path in self.files:
            return self.files[path]
        
        node_id = f"file_{uuid.uuid4().hex[:12]}"
        self.files[path] = node_id
        
        attrs = {
            "node_type": NODE_FILE,
            "path": path,
            "timestamp": datetime.now().isoformat(),
        }
        if mode is not None:
            attrs["mode"] = mode
        if size is not None:
            attrs["size"] = size
        if inode is not None:
            attrs["inode"] = inode
        
        self.graph.add_node(node_id, **attrs)
        return node_id
    
    def add_file_access(self, pid: int, uid: int, path: str, 
                       access_type: str = "READ") -> Optional[Tuple[str, str]]:
        """
        Enregistre un accès fichier (read ou write).
        
        Args:
            pid, uid: Processus qui accède au fichier
            path: Chemin du fichier
            access_type: "READ" ou "WRITE"
            
        Returns:
            (process_node_id, file_node_id) ou None si processus absent
        """
        node_key = (pid, uid)
        if node_key not in self.processes:
            return None
        
        proc_id = self.processes[node_key]
        file_id = self.add_file(path)
        
        # Sélectionner le type d'arête
        relation_type = REL_READS if access_type == "READ" else REL_MODIFIES
        
        # Ajouter ou mettre à jour l'arête
        if self.graph.has_edge(proc_id, file_id):
            self.graph[proc_id][file_id]["count"] = \
                self.graph[proc_id][file_id].get("count", 1) + 1
            self.graph[proc_id][file_id]["last_seen"] = datetime.now().isoformat()
            # Upgrade READ → MODIFIES si l'accès courant est une écriture.
            # Une écriture est plus informative pour le détecteur.
            if relation_type == REL_MODIFIES:
                self.graph[proc_id][file_id]["relation"] = REL_MODIFIES
        else:
            self.graph.add_edge(
                proc_id, file_id,
                relation=relation_type,
                timestamp=datetime.now().isoformat(),
                count=1,
            )
        
        return proc_id, file_id
    
    def add_file_read(self, pid: int, uid: int, path: str) -> Optional[Tuple[str, str]]:
        """Raccourci pour add_file_access avec access_type='READ'."""
        return self.add_file_access(pid, uid, path, access_type="READ")
    
    def add_file_write(self, pid: int, uid: int, path: str) -> Optional[Tuple[str, str]]:
        """Raccourci pour add_file_access avec access_type='WRITE'."""
        return self.add_file_access(pid, uid, path, access_type="WRITE")
    
    # ========================================================================
    # Gestion des Nœuds Socket (Connexions Réseau)
    # ========================================================================
    
    def add_socket(self, ip: str, port: int, protocol: str = "TCP") -> str:
        """
        Ajoute ou récupère un nœud socket.
        
        Args:
            ip: Adresse IP (ou domaine)
            port: Port
            protocol: "TCP" ou "UDP"
            
        Returns:
            node_id
        """
        socket_key = (ip, port)
        if socket_key in self.sockets:
            return self.sockets[socket_key]
        
        node_id = f"socket_{uuid.uuid4().hex[:12]}"
        self.sockets[socket_key] = node_id
        
        self.graph.add_node(
            node_id,
            node_type=NODE_SOCKET,
            ip=ip,
            port=port,
            protocol=protocol,
            timestamp=datetime.now().isoformat(),
        )
        
        return node_id
    
    def add_socket_connection(self, pid: int, uid: int, ip: str, port: int,
                             protocol: str = "TCP") -> Optional[Tuple[str, str]]:
        """
        Enregistre une connexion réseau (tcp_connect event).
        
        Args:
            pid, uid: Processus source
            ip: Destination IP
            port: Destination port
            protocol: "TCP" ou "UDP"
            
        Returns:
            (process_node_id, socket_node_id) ou None
        """
        node_key = (pid, uid)
        if node_key not in self.processes:
            return None
        
        proc_id = self.processes[node_key]
        socket_id = self.add_socket(ip, port, protocol)
        
        # Ajouter l'arête CONNECTS_TO
        if self.graph.has_edge(proc_id, socket_id):
            self.graph[proc_id][socket_id]["count"] = \
                self.graph[proc_id][socket_id].get("count", 1) + 1
            self.graph[proc_id][socket_id]["last_seen"] = datetime.now().isoformat()
        else:
            self.graph.add_edge(
                proc_id, socket_id,
                relation=REL_CONNECTS_TO,
                timestamp=datetime.now().isoformat(),
                count=1,
            )
        
        return proc_id, socket_id
    
    # ========================================================================
    # Requêtes et Snapshots
    # ========================================================================
    
    def get_process_neighbors(self, pid: int, uid: int) -> Dict[str, List[str]]:
        """
        Retourne tous les voisins d'un processus (enfants, fichiers, sockets).
        
        Returns:
            {"children": [node_ids], "files": [node_ids], "sockets": [node_ids]}
        """
        node_key = (pid, uid)
        if node_key not in self.processes:
            return {"children": [], "files": [], "sockets": []}
        
        proc_id = self.processes[node_key]
        result = {"children": [], "files": [], "sockets": []}
        
        for succ_id in self.graph.successors(proc_id):
            edge_data = self.graph[proc_id][succ_id]
            relation = edge_data.get("relation", "UNKNOWN")
            
            if relation == REL_SPAWNS:
                result["children"].append(succ_id)
            elif relation == REL_MODIFIES or relation == REL_READS:
                result["files"].append(succ_id)
            elif relation == REL_CONNECTS_TO:
                result["sockets"].append(succ_id)
        
        return result
    
    def get_graph_snapshot(self) -> Dict[str, Any]:
        """
        Retourne un snapshot exploitable du graphe pour l'Analyste.
        C'est l'interface de contrat vers le module 'analysis'.
        
        Returns:
            {
                "timestamp": ISO datetime,
                "nodes": [{"id": str, "type": str, "attrs": {...}}, ...],
                "edges": [{"source": str, "target": str, "relation": str, ...}, ...],
                "statistics": {"num_processes": int, "num_files": int, ...}
            }
        """
        nodes = []
        edges = []
        
        # Exporter les nœuds
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "type": attrs.get("node_type"),
                "attributes": {k: v for k, v in attrs.items() 
                              if k != "node_type"},
            })
        
        # Exporter les arêtes
        for source, target, attrs in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": attrs.get("relation"),
                "attributes": {k: v for k, v in attrs.items() 
                              if k != "relation"},
            })
        
        # Statistiques
        stats = {
            "num_processes": sum(1 for n in self.graph.nodes(data=True) 
                               if n[1].get("node_type") == NODE_PROCESS),
            "num_files": sum(1 for n in self.graph.nodes(data=True) 
                           if n[1].get("node_type") == NODE_FILE),
            "num_sockets": sum(1 for n in self.graph.nodes(data=True) 
                             if n[1].get("node_type") == NODE_SOCKET),
            "num_edges": len(list(self.graph.edges())),
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "nodes": nodes,
            "edges": edges,
            "statistics": stats,
        }
    
    def _graph_without_none_attrs(self) -> nx.DiGraph:
        """
        Returns a copy of the internal graph with None-valued attributes removed.
        Required for GEXF and GraphML exports, which do not support None values.
        """
        clean = nx.DiGraph()
        for node_id, data in self.graph.nodes(data=True):
            clean.add_node(node_id, **{k: v for k, v in data.items() if v is not None})
        for src, tgt, data in self.graph.edges(data=True):
            clean.add_edge(src, tgt, **{k: v for k, v in data.items() if v is not None})
        return clean

    def export_graph(self, format: str = "json") -> str:
        """
        Exporte le graphe dans divers formats.
        
        Args:
            format: "json", "gexf", ou "graphml"
            
        Returns:
            Représentation sérialisée du graphe
        """
        if format == "json":
            snapshot = self.get_graph_snapshot()
            return json.dumps(snapshot, indent=2, default=str)
        
        elif format == "gexf":
            # GEXF = Graph Exchange XML (pour Gephi)
            # Neither GEXF nor GraphML support None attribute values — build a
            # clean copy with None-valued attributes stripped out.
            # lxml (used by networkx) writes bytes, so we use BytesIO.
            import io
            buf = io.BytesIO()
            nx.write_gexf(self._graph_without_none_attrs(), buf)
            return buf.getvalue().decode("utf-8")

        elif format == "graphml":
            # GraphML = XML-based graph format
            import io
            buf = io.BytesIO()
            nx.write_graphml(self._graph_without_none_attrs(), buf)
            return buf.getvalue().decode("utf-8")
        
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    # ========================================================================
    # Utilitaires de Debug
    # ========================================================================
    
    def print_summary(self):
        """Affiche un résumé du graphe."""
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


if __name__ == "__main__":  # pragma: no cover
    # Test rapide
    sg = SystemGraph()
    
    # Ajouter quelques événements
    sg.add_process_spawn(1, 100, "bash", 1000, 1000, "default")
    sg.add_process_spawn(100, 101, "curl", 1000, 1000, "default")
    sg.add_file_read(100, 1000, "/etc/resolv.conf")
    sg.add_file_write(101, 1000, "/tmp/output.txt")
    sg.add_socket_connection(101, 1000, "8.8.8.8", 443)
    
    sg.print_summary()
    print(json.dumps(sg.get_graph_snapshot(), indent=2, default=str))
