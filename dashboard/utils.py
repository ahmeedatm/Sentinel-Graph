import os
import pandas as pd
from pyvis.network import Network

def get_node_color(node_type):
    if node_type == "PROCESS":
        return "#3b82f6"  # blue
    elif node_type == "FILE":
        return "#10b981"  # green
    elif node_type == "SOCKET":
        return "#8b5cf6"  # purple
    return "#6b7280"

def draw_graph(snapshot: dict, alerts: list) -> str:
    """
    Generate an HTML string representing the PyVis network graph.
    Compromised nodes (involved in alerts) will be colored red.
    """
    # Identify compromised nodes from alerts
    compromised_node_ids = set()
    for alert in alerts:
        evidence = alert.evidence
        if "source_node" in evidence:
            compromised_node_ids.add(evidence["source_node"].get("id"))
        if "target_node" in evidence:
            compromised_node_ids.add(evidence["target_node"].get("id"))

    net = Network(height="600px", width="100%", bgcolor="#1e293b", font_color="white", directed=True)
    # Configure physics for an organic look
    net.force_atlas_2based()

    nodes = snapshot.get("nodes", [])
    edges = snapshot.get("edges", [])

    if not nodes:
        # Return empty graph
        net.write_html("pyvis_graph.html")
        with open("pyvis_graph.html", "r") as f:
            return f.read()

    for node in nodes:
        n_id = node.get("id")
        n_type = node.get("type", "UNKNOWN")
        attrs = node.get("attributes", {})
        
        if n_type == "PROCESS":
            label = attrs.get("comm", str(n_id))
        elif n_type == "FILE":
            label = attrs.get("path", str(n_id)).split("/")[-1]
        elif n_type == "SOCKET":
            label = f"{attrs.get('ip', '')}:{attrs.get('port', '')}"
        else:
            label = str(n_id)

        title_lines = [f"Type: {n_type}", f"ID: {n_id}"]
        title_lines.extend([f"{k}: {v}" for k, v in attrs.items()])
        title = "\n".join(title_lines)
        
        is_compromised = n_id in compromised_node_ids
        color = "#ef4444" if is_compromised else get_node_color(n_type)
        size = 25 if is_compromised else 15

        net.add_node(n_id, label=label, title=title, color=color, size=size)

    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        rel = edge.get("relation", "")
        # Highlight edges that connect two compromised nodes
        e_color = "#ef4444" if (src in compromised_node_ids and tgt in compromised_node_ids) else "#94a3b8"
        net.add_edge(src, tgt, title=rel, label=rel, color=e_color)

    html_file = "pyvis_graph.html"
    net.write_html(html_file)
    with open(html_file, "r") as f:
        html_code = f.read()
    return html_code

def format_alerts(alerts: list) -> pd.DataFrame:
    """
    Format alerts into a pandas DataFrame for Streamlit display.
    """
    if not alerts:
        return pd.DataFrame(columns=["Timestamp", "Severity", "Type", "Process", "Description"])
    
    data = []
    for a in alerts:
        data.append({
            "Timestamp": a.timestamp,
            "Severity": a.severity,
            "Type": a.alert_type,
            "Process": a.process_comm,
            "Description": a.description
        })
    df = pd.DataFrame(data)
    df.sort_values(by="Timestamp", ascending=False, inplace=True)
    return df
