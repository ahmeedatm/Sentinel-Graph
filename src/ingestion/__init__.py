"""
Data Ingestion Module (Le Mapper)
==================================

Ce module est responsable de la transformation des événements bruts
du noyau/Tetragon en une représentation graphe exploitable par
le module d'analyse (l'Analyste).

Modules:
  - constants.py:   Définition du schéma (nœuds, arêtes, mappages)
  - graph_model.py: Classe SystemGraph (structure centrale)
  - collector.py:   Lecteur d'événements JSON (flux Tetragon)

Workflow:
  1. EventCollector lit événements JSON
  2. EventCollector parse et dispatche vers SystemGraph
  3. SystemGraph accumule nœuds et arêtes
  4. SystemGraph.get_graph_snapshot() retourne snapshot pour Analyste

Utilisation simple:
  from ingestion import EventCollector
  
  collector = EventCollector()
  collector.process_json_file("dummy_logs.json")
  snapshot = collector.graph.get_graph_snapshot()
"""

from .graph_model import SystemGraph
from .collector import EventCollector

__all__ = ["SystemGraph", "EventCollector"]
