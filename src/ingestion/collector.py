"""
Phase 4B: Event Collector
==========================

Ce module lit un flux d'événements JSON (simulé ou réel depuis Tetragon)
et les transforme en appels à la classe SystemGraph.

Role:
  - Parser les événements Tetragon (format JSON)
  - Dispatcher vers les méthodes appropriées de SystemGraph
  - Gérer les erreurs et les événements inattendus

Architecture:
  JSON Event → parse() → dispatch() → SystemGraph.method()
  
Exemple flux:
  {"event_type": "process_exec", "pid": 100, "parent_pid": 1, ...}
       ↓
  EventCollector.parse_event()
       ↓
  EventCollector.dispatch_event(parsed_event)
       ↓
  SystemGraph.add_process_spawn(1, 100, ...)
"""

import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import logging

try:
    # Package import: from ingestion import EventCollector
    from .graph_model import SystemGraph
    from .constants import (
        EVENT_PROCESS_EXEC, EVENT_PROCESS_EXIT, EVENT_TCP_CONNECT,
        EVENT_FILE_OPEN, EVENT_FILE_WRITE, EVENT_FILE_READ,
        EVENT_HANDLERS,
    )
except ImportError:
    # Direct script execution: python3 collector.py
    from graph_model import SystemGraph  # type: ignore[no-redef]
    from constants import (  # type: ignore[no-redef]
        EVENT_PROCESS_EXEC, EVENT_PROCESS_EXIT, EVENT_TCP_CONNECT,
        EVENT_FILE_OPEN, EVENT_FILE_WRITE, EVENT_FILE_READ,
        EVENT_HANDLERS,
    )

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class EventCollector:
    """
    Collecteur d'événements. Lit un flux JSON et remplit SystemGraph.
    
    Attributes:
        graph: Instance de SystemGraph
        event_count: Nombre d'événements traités
        error_count: Nombre d'erreurs rencontrées
    """
    
    def __init__(self, graph: Optional[SystemGraph] = None):
        """
        Initialise le collecteur.
        
        Args:
            graph: Objet SystemGraph existant, ou None pour créer une nouvelle instance
        """
        self.graph = graph or SystemGraph()
        self.event_count = 0
        self.error_count = 0
    
    def parse_event(self, json_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse une ligne JSON représentant un événement.
        
        Args:
            json_line: Chaîne JSON
            
        Returns:
            Dictionnaire d'événement, ou None si erreur de parsing
        """
        try:
            event = json.loads(json_line)
            if not isinstance(event, dict):
                logger.warning(f"Event is not a dict: {json_line[:100]}")
                return None
            return event
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e} (line: {json_line[:100]})")
            self.error_count += 1
            return None
    
    def dispatch_event(self, event: Dict[str, Any]) -> bool:
        """
        Dispatch un événement parsé vers SystemGraph.
        
        Args:
            event: Dictionnaire d'événement
            
        Returns:
            True si dispatch réussi, False sinon
        """
        event_type = event.get("event_type")
        
        if event_type == EVENT_PROCESS_EXEC:
            return self._handle_process_exec(event)
        elif event_type == EVENT_PROCESS_EXIT:
            return self._handle_process_exit(event)
        elif event_type == EVENT_TCP_CONNECT:
            return self._handle_tcp_connect(event)
        elif event_type == EVENT_FILE_OPEN:
            return self._handle_file_open(event)
        elif event_type == EVENT_FILE_WRITE:
            return self._handle_file_write(event)
        elif event_type == EVENT_FILE_READ:
            return self._handle_file_read(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return False
    
    # ========================================================================
    # Handlers pour chaque type d'événement
    # ========================================================================
    
    def _handle_process_exec(self, event: Dict[str, Any]) -> bool:
        """Traite un événement process_exec (execve)."""
        try:
            parent_pid = event.get("parent_pid")
            child_pid = event.get("pid")
            comm = event.get("comm", "unknown")
            uid = event.get("uid", 0)
            gid = event.get("gid", 0)
            pod_name = event.get("pod_name")
            namespace = event.get("namespace")
            
            if child_pid is None or parent_pid is None:
                logger.warning(f"Missing pid or parent_pid in: {event}")
                return False
            
            self.graph.add_process_spawn(
                parent_pid, child_pid, comm, uid, gid, pod_name, namespace
            )
            logger.debug(f"Added process spawn: {parent_pid} -> {child_pid} ({comm})")
            return True
        
        except Exception as e:
            logger.error(f"Error handling process_exec: {e}")
            self.error_count += 1
            return False
    
    def _handle_process_exit(self, event: Dict[str, Any]) -> bool:
        """Traite un événement process_exit."""
        try:
            pid = event.get("pid")
            uid = event.get("uid", 0)
            
            if pid is None:
                logger.warning(f"Missing pid in: {event}")
                return False
            
            self.graph.remove_process(pid, uid)
            logger.debug(f"Removed process: {pid}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling process_exit: {e}")
            self.error_count += 1
            return False
    
    def _handle_tcp_connect(self, event: Dict[str, Any]) -> bool:
        """Traite un événement tcp_connect."""
        try:
            pid = event.get("pid")
            uid = event.get("uid", 0)
            ip = event.get("destination_ip")
            port = event.get("destination_port")
            protocol = event.get("protocol", "TCP")
            
            if pid is None or ip is None or port is None:
                logger.warning(f"Missing required fields in: {event}")
                return False
            
            self.graph.add_socket_connection(pid, uid, ip, port, protocol)
            logger.debug(f"Added socket connection: {pid} -> {ip}:{port}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling tcp_connect: {e}")
            self.error_count += 1
            return False
    
    def _handle_file_open(self, event: Dict[str, Any]) -> bool:
        """Traite un événement file_open."""
        try:
            pid = event.get("pid")
            uid = event.get("uid", 0)
            path = event.get("path")
            access_type = event.get("access_type", "READ")
            
            if pid is None or path is None:
                logger.warning(f"Missing pid or path in: {event}")
                return False
            
            self.graph.add_file_access(pid, uid, path, access_type)
            logger.debug(f"Added file access: {pid} {access_type} {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling file_open: {e}")
            self.error_count += 1
            return False
    
    def _handle_file_write(self, event: Dict[str, Any]) -> bool:
        """Traite un événement file_write."""
        try:
            pid = event.get("pid")
            uid = event.get("uid", 0)
            path = event.get("path")
            
            if pid is None or path is None:
                logger.warning(f"Missing pid or path in: {event}")
                return False
            
            self.graph.add_file_write(pid, uid, path)
            logger.debug(f"Added file write: {pid} -> {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling file_write: {e}")
            self.error_count += 1
            return False
    
    def _handle_file_read(self, event: Dict[str, Any]) -> bool:
        """Traite un événement file_read."""
        try:
            pid = event.get("pid")
            uid = event.get("uid", 0)
            path = event.get("path")
            
            if pid is None or path is None:
                logger.warning(f"Missing pid or path in: {event}")
                return False
            
            self.graph.add_file_read(pid, uid, path)
            logger.debug(f"Added file read: {pid} <- {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling file_read: {e}")
            self.error_count += 1
            return False
    
    # ========================================================================
    # Interface publique: traitement de flux
    # ========================================================================
    
    def process_json_file(self, filepath: str) -> int:
        """
        Lit et traite un fichier JSON (array d'événements ou newline-delimited).
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            Nombre d'événements traités avec succès
        """
        path = Path(filepath)
        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return 0
        
        logger.info(f"Processing file: {filepath}")
        
        with open(path, 'r') as f:
            content = f.read().strip()
        
        # Essayer de parser comme array JSON
        if content.startswith('['):
            try:
                events = json.loads(content)
                if not isinstance(events, list):
                    logger.error("JSON is not a list")
                    return 0
                
                for event in events:
                    if isinstance(event, dict):
                        if self.dispatch_event(event):
                            self.event_count += 1
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                return 0
        
        # Sinon, essayer newline-delimited JSON
        else:
            for line in content.split('\n'):
                if not line.strip():
                    continue
                
                event = self.parse_event(line)
                if event and self.dispatch_event(event):
                    self.event_count += 1
        
        logger.info(f"Processing complete. Events: {self.event_count}, Errors: {self.error_count}")
        return self.event_count
    
    def process_stdin(self) -> int:
        """
        Lit depuis stdin (streaming, ligne par ligne).
        
        Returns:
            Nombre d'événements traités
        """
        logger.info("Reading from stdin...")
        
        for line in sys.stdin:
            if not line.strip():
                continue
            
            event = self.parse_event(line)
            if event and self.dispatch_event(event):
                self.event_count += 1
        
        logger.info(f"Processing complete. Events: {self.event_count}, Errors: {self.error_count}")
        return self.event_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de collecte."""
        return {
            "events_processed": self.event_count,
            "errors": self.error_count,
            "graph_snapshot": self.graph.get_graph_snapshot(),
        }


# ============================================================================
# Script principal
# ============================================================================

if __name__ == "__main__":  # pragma: no cover
    import argparse
    
    parser = argparse.ArgumentParser(description="Tetragon Event Collector")
    parser.add_argument("--input", type=str, help="JSON input file (default: stdin)")
    parser.add_argument("--output", type=str, help="Output file for graph snapshot (JSON)")
    parser.add_argument("--format", choices=["json", "gexf", "graphml"], 
                       default="json", help="Graph export format")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Créer le collecteur
    collector = EventCollector()
    
    # Traiter les événements
    if args.input:
        collector.process_json_file(args.input)
    else:
        collector.process_stdin()
    
    # Afficher le résumé
    collector.graph.print_summary()
    
    # Exporter si demandé
    if args.output:
        output_data = collector.graph.export_graph(format=args.format)
        with open(args.output, 'w') as f:
            f.write(output_data)
        logger.info(f"Graph exported to: {args.output}")
    
    # Afficher les stats finales
    stats = collector.get_statistics()
    print(f"\nStatistics:")
    print(f"  Events processed: {stats['events_processed']}")
    print(f"  Errors: {stats['errors']}")
