"""
Phase 2: Schéma de Modélisation Graphe
========================================

Ce module définit le "dictionnaire" de conversion des événements Tetragon
en structures graphe (nœuds et arêtes). Il formalise le contrat entre
le flux brut et la représentation exploitable par l'Analyste.

Architecture:
  Événement Tetragon (JSON) → Parser → Type d'événement → Appels SystemGraph
  
Exemple de mappage:
  ┌──────────────────────────────────────────────────────────────┐
  │ Événement         │ Nœud Source  │ Arête      │ Nœud Cible   │
  ├──────────────────────────────────────────────────────────────┤
  │ execve            │ Processus    │ SPAWNS     │ Processus    │
  │ tcp_connect       │ Processus    │ CONNECTS   │ Socket       │
  │ open / write      │ Processus    │ MODIFIES   │ Fichier      │
  │ open / read       │ Processus    │ READS      │ Fichier      │
  └──────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# Types de Nœuds (Node Types)
# ============================================================================

NODE_PROCESS = "process"
NODE_FILE = "file"
NODE_SOCKET = "socket"
NODE_POD = "pod"

# ============================================================================
# Types de Relations / Arêtes (Edge Types)
# ============================================================================

REL_SPAWNS = "SPAWNS"              # Processus Père -> Processus Fils (execve)
REL_CONNECTS_TO = "CONNECTS_TO"    # Processus -> Socket (connexion réseau)
REL_MODIFIES = "MODIFIES"          # Processus -> Fichier (write/truncate)
REL_READS = "READS"                # Processus -> Fichier (read/open RO)
REL_CONTAINS = "CONTAINS"          # Pod -> Processus (contexte K8s)

# ============================================================================
# Types d'Événements Tetragon Supportés
# ============================================================================

EVENT_PROCESS_EXEC = "process_exec"           # Exécution de processus (execve)
EVENT_PROCESS_EXIT = "process_exit"           # Terminaison de processus
EVENT_PROCESS_KPROBE = "process_kprobe"       # Kprobe générique (fichier, réseau)
EVENT_TCP_CONNECT = "tcp_connect"             # Connexion TCP établie
EVENT_TCP_LISTEN = "tcp_listen"               # Port en écoute
EVENT_FILE_OPEN = "file_open"                 # Accès fichier (open syscall)
EVENT_FILE_WRITE = "file_write"               # Écriture fichier
EVENT_FILE_READ = "file_read"                 # Lecture fichier

# ============================================================================
# Attributs de Nœud (Node Attributes)
# ============================================================================

# Processus
ATTR_PID = "pid"
ATTR_PPID = "parent_pid"
ATTR_COMM = "comm"                # Nom du processus (ex: "bash")
ATTR_UID = "uid"
ATTR_GID = "gid"
ATTR_TIMESTAMP = "timestamp"      # Quand le nœud a été créé
ATTR_POD_NAME = "pod_name"        # K8s pod name
ATTR_NAMESPACE = "namespace"      # K8s namespace
ATTR_CONTAINER_ID = "container_id"

# Fichier
ATTR_PATH = "path"
ATTR_MODE = "mode"                # Permissions (octal)
ATTR_SIZE = "size"
ATTR_INODE = "inode"

# Socket
ATTR_IP = "ip"
ATTR_PORT = "port"
ATTR_PROTOCOL = "protocol"        # TCP, UDP, etc.

# ============================================================================
# Attributs d'Arête (Edge Attributes)
# ============================================================================

EDGE_ATTR_TIMESTAMP = "timestamp"
EDGE_ATTR_COUNT = "count"          # Nombre d'occurrences
EDGE_ATTR_LAST_SEEN = "last_seen"

# ============================================================================
# Constantes de Configuration
# ============================================================================

# Temps d'expiration des nœuds inactifs (en secondes, pour futur cleanup)
TTL_PROCESS = 3600                 # 1 heure
TTL_CONNECTION = 600               # 10 minutes

# Seuils d'anomalie pour l'Analyste
BASELINE_THRESHOLD = 0.8           # Confiance requise
ANOMALY_THRESHOLD = 0.7            # Alerte si écart > 0.7

# ============================================================================
# Mappages Événement → Méthodes SystemGraph
# ============================================================================

# Utilisé par le Collector pour dispatcher les événements
EVENT_HANDLERS = {
    EVENT_PROCESS_EXEC: "add_process_spawn",
    EVENT_PROCESS_EXIT: "remove_process",
    EVENT_TCP_CONNECT: "add_socket_connection",
    EVENT_FILE_OPEN: "add_file_access",
    EVENT_FILE_WRITE: "add_file_write",
    EVENT_FILE_READ: "add_file_read",
}
