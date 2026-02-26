# 🏗️ Infrastructure & Observabilité eBPF (Tetragon)

Ce dossier contient l'ensemble de la configuration nécessaire pour déployer l'environnement de capture d'événements noyau via **eBPF** et **Kubernetes**.

## 📋 Prérequis Système

Le projet doit être exécuté **exclusivement sous Linux** pour permettre l'accès aux fonctionnalités eBPF du noyau.

### Dépendances à installer manuellement :

Avant de lancer le déploiement, installez les outils suivants sur votre machine hôte :

| Outil | Rôle | Commande d'installation |
| --- | --- | --- |
| **Docker** | Moteur de conteneurs | `sudo apt install docker.io -y` |
| **Kind** | Cluster K8s local | `curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && chmod +x ./kind && sudo mv ./kind /usr/local/bin/` |
| **kubectl** | CLI Kubernetes | `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && sudo mv kubectl /usr/local/bin/` |
| **Helm** | Gestionnaire K8s | `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3`

---

## 🚀 Déploiement Automatisé

L'installation de l'infrastructure est pilotée par le script `install.sh`. Il réalise les actions suivantes :

1. Création du cluster **Kind** avec montage des headers du noyau.
2. Installation du DaemonSet **Tetragon** via Helm.
3. Attente du démarrage des services et des **CRD** (Custom Resource Definitions).
4. Application des **TracingPolicies** de filtrage.

# Se placer dans le dossier
cd infra/tetragon/

# Donner les droits et lancer
chmod +x install.sh
./install.sh

---

## 🛡️ Configuration du Traçage (TracingPolicies)

Les politiques définies dans le dossier `policies/` limitent le "bruit" pour ne remonter que les événements critiques au moteur d'analyse Python :

* **`trace-exec.yaml`** : Surveille l'appel système `sys_execve`. Permet de voir chaque nouveau binaire lancé sur le système.
* **`trace-tcp.yaml`** : Surveille `tcp_connect`. Permet d'identifier les communications réseau, les scans de ports ou les reverse shells.

---

## 📥 Flux de données pour le service Python

C'est l'interface entre l'**Infrastructure (Ops)** et le **Moteur d'Analyse (Dév)**.
Le flux JSON brut est accessible via les logs de Tetragon. Pour le transmettre au collecteur Python en temps réel :

kubectl logs -n kube-system -l app.kubernetes.io/name=tetragon -c export-stdout -f

**Format du JSON généré :**

```json
{
  "process_exec": {
    "process": {
      "exec_id": "Mjg0NDU0MjAyOTkyNjo2Nzk5",
      "pid": 6799,
      "binary": "/usr/bin/apt",
      "user": "root"
    }
  },
  "node_name": "ebpf-lab-control-plane",
  "time": "2026-02-26T14:25:00Z"
}

```

---

## 🧹 Nettoyage de l'environnement

Pour supprimer le cluster et libérer les ressources de la machine :

kind delete cluster --name ebpf-lab

---

