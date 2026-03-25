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

echo "--- INFRASTRUCTURE PRETE ---"
echo "Tetragon expose un flux gRPC sur le port 50051"
