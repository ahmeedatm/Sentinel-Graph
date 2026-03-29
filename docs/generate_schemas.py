import os
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

os.makedirs('docs/images', exist_ok=True)

def generate_performance_chart():
    # 1. Performance Bar Chart (eBPF vs Auditd/strace overhead)
    labels = ['strace (ptrace)', 'Auditd', 'Falco (Userspace)', 'Tetragon (In-Kernel eBPF)']
    cpu_usage = [45.2, 15.5, 12.0, 1.8] 
    latency = [12.5, 4.1, 3.2, 0.4]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # CPU Bars
    rects1 = ax1.bar(x - width/2, cpu_usage, width, label='Surcharge CPU (%)', color='#ff9999', edgecolor='black')
    
    # Latency Bars
    ax2 = ax1.twinx()
    rects2 = ax2.bar(x + width/2, latency, width, label='Latence Induite (ms)', color='#66b3ff', edgecolor='black')

    ax1.set_ylabel('Surcharge CPU (%)', color='#cc0000', fontweight='bold')
    ax2.set_ylabel('Latence Induite (ms)', color='#0055cc', fontweight='bold')
    ax1.set_title("Comparatif de Performance : L'Avantage de l'In-Kernel eBPF", fontsize=14, fontweight='bold', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontweight='bold')
    
    # Legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('docs/images/performance_comparison.png', dpi=300)
    plt.close()
    print("✓docs/images/performance_comparison.png généré.")

def generate_threat_graph():
    # 2. Threat Detection Graph (Baseline vs Anomaly)
    G = nx.DiGraph()

    # Nœuds Baseline
    G.add_node("bash\n(Légitime)", color='#99ff99')
    G.add_node("ls\n(Légitime)", color='#99ff99')
    
    # Nœuds Anomalie
    G.add_node("curl\n(Anomalie)", color='#ff9999')
    G.add_node("10.15.22.4:443\n(Serveur C2)", color='#ff4d4d')
    G.add_node("/etc/shadow\n(Fichier Sensible)", color='#ffcc99')

    # Arêtes Baseline
    G.add_edge("bash\n(Légitime)", "ls\n(Légitime)", label="execve\n(Connu)")
    
    # Arêtes Anomalies
    G.add_edge("bash\n(Légitime)", "curl\n(Anomalie)", label="execve\n[UNEXPECTED_SPAWN]")
    G.add_edge("curl\n(Anomalie)", "10.15.22.4:443\n(Serveur C2)", label="tcp_connect\n[UNKNOWN_DESTINATION]")
    G.add_edge("curl\n(Anomalie)", "/etc/shadow\n(Fichier Sensible)", label="openat\n[UNEXPECTED_READ]")

    colors = [node[1]['color'] for node in G.nodes(data=True)]
    
    # Positionnement manuel pour plus de clarté
    pos = {
        "bash\n(Légitime)": (0, 0),
        "ls\n(Légitime)": (-1, 1),
        "curl\n(Anomalie)": (1, 1),
        "10.15.22.4:443\n(Serveur C2)": (2, 0),
        "/etc/shadow\n(Fichier Sensible)": (2, 2)
    }

    plt.figure(figsize=(12, 8))
    
    # Dessin des composants
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=4000, edgecolors='black', linewidths=2)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")
    
    # Flèches
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=25, width=2)
    
    # Étiquettes de flèches
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, font_color='darkred')

    plt.title("Mécanisme de Détection d'Anomalies : Déviation du Sous-Graphe Causal", fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('docs/images/threat_detection_graph.png', dpi=300)
    plt.close()
    print("✓docs/images/threat_detection_graph.png généré.")

if __name__ == "__main__":
    generate_performance_chart()
    generate_threat_graph()
    print("Génération terminée avec succès.")
