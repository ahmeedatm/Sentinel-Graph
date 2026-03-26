#!/bin/bash

# Capture les signaux d'arrêt (Ctrl+C) pour tuer proprement tous les processus enfants branchés
trap 'echo -e "\n🛑 Arrêt de Sentinel-Graph..."; kill $(jobs -p) 2>/dev/null; exit' EXIT INT TERM

echo "🛡️  Démarrage de Sentinel-Graph..."
echo "==================================="

echo "🔌 1. Connexion au flux gRPC de Tetragon (Port-Forwarding en arrière-plan)..."
kubectl port-forward -n kube-system ds/tetragon 54321:54321 > /dev/null 2>&1 &

# Pause courte pour assurer la stabilité du socket
sleep 3

echo "📊 2. Lancement du Dashboard interactif Streamlit..."
streamlit run dashboard/app.py

# Attend indéfiniment jusqu'à la fermeture de Streamlit
wait
