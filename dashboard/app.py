import streamlit as st
import threading
import time
import sys
import os
import pandas as pd

# Adjust paths to import src modules
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)
sys.path.insert(0, os.path.join(src_path, 'ingestion'))
sys.path.insert(0, os.path.join(src_path, 'ingestion', 'proto'))

from ingestion.collector import EventCollector
from analysis.baseline import BaselineLearner
from analysis.detector import AnomalyDetector
from utils import draw_graph, format_alerts
import streamlit.components.v1 as components

# Configure page
st.set_page_config(page_title="Sentinel-Graph Dashboard", page_icon="🛡️", layout="wide")

# Custom CSS for modern styling
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0f172a;
    }
    
    /* Hide top header padding to maximize space */
    .css-18e3th9 {
        padding-top: 2rem;
    }
    
    /* Metrics container styling */
    .metric-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        text-align: center;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
        margin-bottom: 1rem;
    }
    .metric-container:hover {
        transform: translateY(-2px);
    }
    
    /* Values and labels */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -0.025em;
    }
    .metric-label {
        font-size: 0.875rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }
    
    /* Highlights */
    .value-red { color: #ef4444; }
    .value-blue { color: #3b82f6; }
    
    /* Streamlit overrides */
    h1, h2, h3 { color: #f1f5f9 !important; }
    .stDataFrame { border-radius: 0.5rem; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

# ----------------- App State Initialization -----------------
if "grpc_thread" not in st.session_state:
    st.session_state.collector = EventCollector()
    
    # Initialize baseline learner
    learner = BaselineLearner()
    storage_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'analysis', 'storage', 'baseline.json')
    try:
        if os.path.exists(storage_path):
            learner.load(storage_path)
    except Exception as e:
        st.sidebar.error(f"Could not load baseline: {e}")
        
    st.session_state.baseline = learner
    st.session_state.detector = AnomalyDetector(learner)
    
    # Lock for thread safety on graph and detector
    st.session_state.lock = threading.Lock()
    
    # Wrap standard dispatch to be thread-safe
    original_dispatch = st.session_state.collector.dispatch_event
    thread_lock = st.session_state.lock
    def thread_safe_dispatch(event):
        with thread_lock:
            return original_dispatch(event)
    st.session_state.collector.dispatch_event = thread_safe_dispatch
    
    # Background thread function bypassing session_state
    local_collector = st.session_state.collector
    
    def grpc_listener(clctr):
        grpc_addr = os.getenv("TETRAGON_GRPC_ADDRESS", "localhost:54321")
        # Blocks and streams events indefinitely, reconnects on drop
        while True:
            try:
                clctr.process_grpc_stream(address=grpc_addr)
            except Exception as e:
                pass
            time.sleep(5)
            
    thread = threading.Thread(target=grpc_listener, args=(local_collector,), daemon=True)
    thread.start()
    st.session_state.grpc_thread = thread

# --------------------- Auto Refresh -----------------------
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

# ----------------- UI Layout -----------------
st.title("🛡️ Sentinel-Graph : Live Dashboard")

with st.sidebar:
    st.header("⚙️ Configuration")
    is_alive = st.session_state.grpc_thread.is_alive()
    st.markdown(f"**gRPC Stream Status:** {'🟢 Active' if is_alive else '🔴 Inactive'}")
    
    refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2)
    toggle_refresh = st.checkbox("Enable Auto-Refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = toggle_refresh

    st.divider()
    if st.button("💉 Inject Mock Traffic (Offline Test)"):
        import random
        pid = random.randint(1000, 9999)
        mock_event = {
            "event_type": "process_exec",
            "pid": pid,
            "parent_pid": 1,
            "comm": "suspicious_miner",
            "uid": 0,
            "gid": 0,
            "pod_name": "web-server",
            "namespace": "default"
        }
        st.session_state.collector.dispatch_event(mock_event)
        mock_network = {
            "event_type": "tcp_connect",
            "pid": pid,
            "destination_ip": "185.15.20.10",
            "destination_port": 4444,
            "protocol": "TCP"
        }
        st.session_state.collector.dispatch_event(mock_network)
        st.success("Trafic factice injecté !")

# Safely compute metrics
with st.session_state.lock:
    snapshot = st.session_state.collector.graph.get_graph_snapshot()
    # Run anomaly detector internally on the snapshot state
    _ = st.session_state.detector.detect(snapshot)
    all_alerts = list(st.session_state.detector.alerts)

nodes_count = len(snapshot.get("nodes", []))
edges_count = len(snapshot.get("edges", []))
events_count = st.session_state.collector.event_count

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="metric-container"><div class="metric-value value-blue">{events_count}</div><div class="metric-label">Events Processed</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-container"><div class="metric-value">{nodes_count}</div><div class="metric-label">Active Nodes</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-container"><div class="metric-value">{edges_count}</div><div class="metric-label">Active Edges</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-container"><div class="metric-value value-red">{len(all_alerts)}</div><div class="metric-label">Total Alerts</div></div>', unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns([5, 3])

with col1:
    st.subheader("🌐 Real-time Behavioral Graph")
    # Draw graph
    html_code = draw_graph(snapshot, all_alerts)
    components.html(html_code, height=600)

with col2:
    st.subheader("🚨 Detected Anomalies")
    df_alerts = format_alerts(all_alerts)
    
    if not df_alerts.empty:
        # Avoid pandas applymap warning by using map
        if hasattr(df_alerts.style, "map"):
            # newer pandas
            styled_df = df_alerts.style.map(
                lambda v: 'color: #f82b2b; font-weight: bold;' if v == 'HIGH' else 'color: #fb923c; font-weight: bold;', 
                subset=['Severity']
            )
        else:
            # older pandas (1.3.0+)
            styled_df = df_alerts.style.applymap(
                lambda v: 'color: #f82b2b; font-weight: bold;' if v == 'HIGH' else 'color: #fb923c; font-weight: bold;', 
                subset=['Severity']
            )
        st.dataframe(styled_df, height=550, use_container_width=True)
    else:
        st.info("No anomalies detected yet. System behaves normally.", icon="ℹ️")

# Refresh mechanism
if st.session_state.auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
