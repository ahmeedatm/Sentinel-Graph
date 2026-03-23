#!/bin/bash
set -e

# Définition des dossiers
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
INFRA_DIR=$(dirname "$SCRIPT_DIR")

echo "--- 1. Creation du cluster Kind ---"
if kind get clusters | grep -q "^ebpf-lab$"; then
    echo "Le cluster existe deja."
else
    kind create cluster --config "$INFRA_DIR/k8s/kind-config.yaml" --name ebpf-lab
fi

echo "--- 2. Installation de Tetragon via Helm ---"
helm repo add cilium https://helm.cilium.io > /dev/null 2>&1
helm repo update > /dev/null 2>&1
helm upgrade --install tetragon cilium/tetragon -n kube-system \
  --set tetragon.hostNetwork=true \
  --set tetragon.observer.grpcPort=50051

echo "--- 3. Attente du demarrage de Tetragon ---"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=tetragon -n kube-system --timeout=120s

echo "--- 4. Application des politiques eBPF ---"
sleep 10
kubectl apply -f "$INFRA_DIR/policies/"

echo "--- 5. Installation du serveur HTTP pour exposer les events JSON ---"
# Crée un dossier temporaire pour le serveur
SERVER_DIR="$INFRA_DIR/tetragon-http"
mkdir -p "$SERVER_DIR"

cat > "$SERVER_DIR/server.py" << 'EOF'
from flask import Flask, jsonify
import subprocess
import threading
import queue
import json

app = Flask(__name__)
events = queue.Queue()

def watch_tetragon():
    proc = subprocess.Popen(
        ["tetragon-cli", "watch", "--json"],
        stdout=subprocess.PIPE,
        text=True
    )
    for line in proc.stdout:
        try:
            events.put(json.loads(line))
        except json.JSONDecodeError:
            continue

threading.Thread(target=watch_tetragon, daemon=True).start()

@app.route("/events")
def get_events():
    result = []
    while not events.empty():
        result.append(events.get())
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
EOF

echo "--- 6. Lancement du serveur HTTP ---"
# Installe Flask si besoin
pip3 install --quiet flask || true
# Lancement en arrière-plan
nohup python3 "$SERVER_DIR/server.py" > "$SERVER_DIR/server.log" 2>&1 &

echo "--- INFRASTRUCTURE PRETE ---"
echo "Le serveur HTTP pour les events JSON tourne sur le port 8080"
