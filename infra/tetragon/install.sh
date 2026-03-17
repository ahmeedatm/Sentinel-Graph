#!/bin/bash
set -e

# --- CONFIGURATION DES CHEMINS ---
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_INFRA=$(dirname "$SCRIPT_DIR")

echo "========================================================"
echo "DÉPLOIEMENT INFRASTRUCTURE TETRAGON & EBPF"
echo "========================================================"

echo "🚀 1. CLUSTER KIND"
if kind get clusters | grep -q "^ebpf-lab$"; then
    echo "CLUSTER ALREADY HERE"
else
    kind create cluster --config "$PROJECT_INFRA/k8s/kind-config.yaml" --name ebpf-lab
fi

echo "2. HELM INSTALL"
helm repo add cilium https://helm.cilium.io > /dev/null 2>&1
helm repo update > /dev/null 2>&1
helm upgrade --install tetragon cilium/tetragon -n kube-system --set tetragon.hostNetwork=true

echo "3. WAITING PODS"
# On attend que le pod soit au moins créé
until kubectl get pods -n kube-system -l app.kubernetes.io/name=tetragon 2>/dev/null | grep -q "tetragon"; do
    echo "Recherche du Pod Tetragon..."
    sleep 2
done
# On attend qu'il soit prêt
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=tetragon -n kube-system --timeout=120s

echo "4. ENREGISTREMENT CRD & POLITIQUES"
# BOUCLE CRUCIALE : On attend que le CRD soit reconnu par l'API
echo "Attente de l'enregistrement des CRD Tetragon..."
MAX_RETRIES=10
COUNT=0
until kubectl get crd tracingpolicies.cilium.io > /dev/null 2>&1; do
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR : The CRD could not be installed in time."
        exit 1
    fi
    echo "Tentative $COUNT/$MAX_RETRIES : CRD non trouvé, attente..."
    sleep 5
done

# Une fois le CRD trouvé, on attend qu'il soit "établi"
kubectl wait --for condition=established --timeout=60s crd/tracingpolicies.cilium.io

if [ -d "$PROJECT_INFRA/policies/" ]; then
    echo "Application des politiques..."
    kubectl apply -f "$PROJECT_INFRA/policies/"
    echo "Policies are apply"
else
    echo "Error : Policies folder not found"
    exit 1
fi

echo "========================================================"
echo "INFRA READY"
echo "========================================================"
