# 📥 Data Ingestion Module — "Le Mapper" (Architecte de Données)

## 📋 Overview

This module is the **bridge between raw system events and intelligent analysis**. As the Data Architect ("Le Mapper"), your role is to transform Tetragon's JSON event stream into a graph structure that the Analyst can reason about.

**Core Responsibility:**
> Without you, Tetragon event logs are just unreadable text lines. You are the translator who builds understanding.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Raw Tetragon Events (JSON Stream)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ EventCollector (collector.py)                           │
│  • Parses JSON                                           │
│  • Dispatches to appropriate handlers                    │
│  • Manages error recovery                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Calls methods on
                     ▼
┌─────────────────────────────────────────────────────────┐
│ SystemGraph (graph_model.py)                            │
│  • add_process_spawn()                                   │
│  • add_file_access()                                     │
│  • add_socket_connection()                               │
│  • get_graph_snapshot()                                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ Graph Snapshot (Nodes + Edges)                          │
│ ↓ Passed to Analyst (analysis module)                   │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Files

### `constants.py`
**The Schema Dictionary**

Defines the complete mapping of:
- **Node Types**: `process`, `file`, `socket`, `pod`
- **Edge Types (Relations)**: `SPAWNS`, `MODIFIES`, `READS`, `CONNECTS_TO`, `CONTAINS`
- **Event Types**: `process_exec`, `tcp_connect`, `file_open`, `file_write`, etc.
- **Node Attributes**: pid, ppid, comm, uid, path, ip, port, etc.
- **Event Handlers Mapping**: Which method handles which event type

This is the **formal contract** between raw events and graph representation.

### `graph_model.py`
**The SystemGraph Class**

Core data structure managing the behavioral graph:

```python
class SystemGraph:
    # Add processes (with spawn relationships)
    add_process_spawn(parent_pid, child_pid, comm, uid, gid)
    
    # Add file accesses (read/write)
    add_file_read(pid, uid, path)
    add_file_write(pid, uid, path)
    
    # Add network connections
    add_socket_connection(pid, uid, ip, port, protocol)
    
    # Query the graph
    get_process_neighbors(pid, uid)
    
    # Export for Analyst
    get_graph_snapshot()  # → Returns JSON-serializable dict
    
    # Export graph in various formats
    export_graph(format="json" | "gexf" | "graphml")
```

**Key Features:**
- Uses NetworkX DiGraph internally (directed graph)
- Caching for fast lookups: processes, files, sockets
- Automatic node ID generation with UUIDs
- Edge attributes: timestamp, count, last_seen

### `collector.py`
**The Event Stream Reader**

Transforms JSON event stream → SystemGraph:

```python
class EventCollector:
    # Initialize with SystemGraph
    __init__(graph=None)
    
    # Parse and dispatch events
    process_json_file(filepath)
    process_stdin()
    
    # Individual event handlers (private)
    _handle_process_exec(event)
    _handle_tcp_connect(event)
    _handle_file_write(event)
    ...
    
    # Get final statistics
    get_statistics()
```

**Features:**
- Parses JSON (both array and newline-delimited formats)
- Error handling and recovery
- Detailed logging for debugging
- Statistics tracking (events processed, errors)
- CLI interface with arguments

### `dummy_logs.json`
**Test Data**

Realistic Tetragon-like event logs for development/testing:
- Process spawns (bash → curl → python3)
- File accesses (read /etc/resolv.conf, write /tmp/output.txt)
- Network connections (curl to 8.8.8.8:443, python3 to 192.168.1.100:5432)

---

## 🚀 Quick Start

### 1. Test the Graph Model Directly

```bash
cd src/ingestion
python3 graph_model.py
```

**Output**: Prints graph summary + full JSON snapshot of test data.

### 2. Process Dummy Logs

```bash
python3 collector.py --input dummy_logs.json --output snapshot.json --verbose
```

**Output**: 
- Logs all events processed
- Creates `snapshot.json` with full graph
- Prints statistics

### 3. Use in Your Code

```python
from ingestion import EventCollector, SystemGraph

# Initialize
collector = EventCollector()

# Process events from file
collector.process_json_file("my_tetragon_logs.json")

# Get the built graph
graph = collector.graph
snapshot = graph.get_graph_snapshot()

# Use snapshot data
num_processes = snapshot["statistics"]["num_processes"]
nodes = snapshot["nodes"]
edges = snapshot["edges"]

# Pass to Analyst
pass_to_analyst(snapshot)
```

### 4. Real-Time Streaming (from Tetragon)

```bash
# If Tetragon outputs to stdout:
tetragon-events | python3 collector.py --output live_snapshot.json
```

---

## 📊 Event Schema

### Mapping: Event Type → SystemGraph Methods

| Event Type | Handler | Calls | Creates |
|-----------|---------|-------|---------|
| `process_exec` | `_handle_process_exec()` | `add_process_spawn()` | Processes + SPAWNS edge |
| `process_exit` | `_handle_process_exit()` | `remove_process()` | Cleans up node |
| `tcp_connect` | `_handle_tcp_connect()` | `add_socket_connection()` | Socket + CONNECTS_TO edge |
| `file_open` | `_handle_file_open()` | `add_file_access()` | File + READ/WRITE edge |
| `file_write` | `_handle_file_write()` | `add_file_write()` | File + MODIFIES edge |
| `file_read` | `_handle_file_read()` | `add_file_read()` | File + READS edge |

### Input Event Format (JSON)

```json
{
  "timestamp": "2026-02-06T10:15:30Z",
  "event_type": "process_exec",
  "pid": 101,
  "parent_pid": 100,
  "comm": "curl",
  "uid": 1000,
  "gid": 1000,
  "pod_name": "default-pod",
  "namespace": "default"
}
```

### Output: Graph Snapshot

```json
{
  "timestamp": "2026-02-06T16:20:58.912681",
  "nodes": [
    {
      "id": "proc_100_1000_93df3097",
      "type": "process",
      "attributes": {
        "pid": 100,
        "parent_pid": null,
        "comm": "bash",
        "uid": 1000,
        "gid": 1000,
        "timestamp": "2026-02-06T16:20:58.912257",
        "pod_name": "default-pod",
        "namespace": "default"
      }
    }
  ],
  "edges": [
    {
      "source": "proc_100_1000_93df3097",
      "target": "proc_101_1000_9a8e8e3e",
      "relation": "SPAWNS",
      "attributes": {
        "timestamp": "2026-02-06T16:20:58.912389",
        "count": 1
      }
    }
  ],
  "statistics": {
    "num_processes": 4,
    "num_files": 4,
    "num_sockets": 2,
    "num_edges": 9
  }
}
```

---

## 🔄 Workflow Example

**Input Event:**
```json
{"event_type": "process_exec", "pid": 102, "parent_pid": 101, "comm": "python3", "uid": 1000, ...}
```

**Processing Steps:**

1. **EventCollector.process_json_file()** reads the JSON
2. **EventCollector.parse_event()** converts to dict
3. **EventCollector.dispatch_event()** identifies type = `process_exec`
4. **EventCollector._handle_process_exec()** extracts fields
5. **SystemGraph.add_process_spawn()** is called
   - Ensures parent process exists (or creates it)
   - Adds child process node
   - Creates SPAWNS edge
6. **SystemGraph.get_graph_snapshot()** exported for Analyst

**Result:** A directed edge from "parent process 101" → "child process 102" with relation type "SPAWNS".

---

## 🧪 Testing

### Unit Test: Graph Model

```bash
python3 graph_model.py
# Adds test processes/files/sockets and displays snapshot
```

**Expected Output:**
```
SystemGraph Summary - 2026-02-06T16:20:54.608669
============================================================
  Processus: 3
  Fichiers:  2
  Sockets:   1
  Arêtes:    5
============================================================
```

### Integration Test: Collector + Dummy Logs

```bash
python3 collector.py --input dummy_logs.json --verbose
# Should process 9 events with 0 errors
```

---

## 🔧 Advanced Usage

### Export Graph in Different Formats

```bash
# JSON (default)
python3 collector.py --input logs.json --output graph.json --format json

# GEXF (for Gephi visualization)
python3 collector.py --input logs.json --output graph.gexf --format gexf

# GraphML (for yEd, Cytoscape)
python3 collector.py --input logs.json --output graph.graphml --format graphml
```

### Verbose Logging

```bash
python3 collector.py --input logs.json --verbose
# Prints DEBUG level logs for each event processed
```

### Stream Processing (Real-Time)

```bash
# Assuming Tetragon outputs JSON to stdout:
tetragon | python3 -c "
from ingestion import EventCollector
collector = EventCollector()
collector.process_stdin()
collector.graph.print_summary()
"
```

---

## 🚀 Next Steps: Integration with Analyst

Once the graph is built, pass the snapshot to the **Analysis Module**:

```python
# In src/analysis/detector.py (the Analyst's code)
from ingestion import EventCollector

collector = EventCollector()
collector.process_json_file("tetragon_events.json")

snapshot = collector.graph.get_graph_snapshot()

# Analyst now uses snapshot to:
# 1. Compare against baseline
# 2. Detect anomalies
# 3. Generate alerts
detector = AnomalyDetector()
alerts = detector.detect(snapshot)
```

---

## 📚 Dependencies

- **NetworkX**: Graph structure & algorithms
- **json5**: Extended JSON parsing (optional, for flexibility)
- **python-json-logger**: Structured logging (optional)
- Python 3.9+

All included in `requirement.txt`.

---

## 📝 Notes

### Design Decisions

1. **NetworkX over Neo4j**: Start simple, in-memory. Scale to Neo4j later if needed.
2. **UUID node IDs**: Ensures uniqueness even with process reuse (PID wrapping).
3. **Caching by (pid, uid)**: Fast lookups without scanning entire graph.
4. **Snapshot over streaming**: Analyst gets consistent point-in-time view.

### Performance Considerations

- Graph grows linearly with events: O(n) space, O(1) lookup
- For > 100k nodes, consider Neo4j backend
- Snapshot export is O(n) but parallelizable

### Extensibility

To add new event types:

1. Add constant to `constants.py` → `EVENT_NEW_TYPE`
2. Add handler to `collector.py` → `_handle_new_type()`
3. Add method to `SystemGraph` → `add_new_relation()`
4. Add to `EVENT_HANDLERS` mapping in constants

---

## 👤 Author

**"Le Mapper" — Data Architect**

Your job is to build the bridge. Make it clear, robust, and fast. ✨

---

**Status**: ✅ Phase 1-5 Complete
**Tests**: ✅ Passing
**Ready for**: Integration with Analysis Module
