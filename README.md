# 📂 Architecture du Projet

Ce projet implémente une solution de **détection d'intrusion basée sur des graphes comportementaux** exploitant eBPF et Kubernetes. L'architecture modulaire sépare clairement les préoccupations entre l'infrastructure, l'ingestion de données, l'analyse et la visualisation.

## 🗂️ Arborescence du Projet

```
Sentinel-Graph/
├── docs/                   # Documentation académique et technique
├── infra/                  # Configuration Kubernetes et politiques Tetragon
│   ├── k8s/                # Manifestes Kubernetes
│   ├── tetragon/           # Configuration DaemonSet Tetragon
│   └── policies/           # Politiques de traçage (TracingPolicies)
├── src/                    # Code source principal (Backend)
│   ├── ingestion/          # Transformation des logs en graphes
│   └── analysis/           # Moteur de détection d'anomalies
├── dashboard/              # Interface de visualisation (Frontend)
├── red_team/               # Scénarios d'attaque et validation
├── requirement.txt         # Dépendances Python
└── README.md               # Ce fichier
```

## 📚 Détails des Modules

### 1. docs/ — Documentation & Recherche
**Contient l'étude théorique et la documentation technique du projet :**

- **cahier_des_charges.tex** — Spécifications détaillées des besoins et objectifs
- **etat_de_lart.tex** — État de l'art sur l'observabilité, les graphes de comportement et eBPF
- **tetragon_specs.md** — Documentation technique du fonctionnement interne de Tetragon

### 2. infra/ — Infrastructure & eBPF
**Contient toute la configuration d'infrastructure et de surveillance :**

- **k8s/** — Manifestes Kubernetes pour déployer un cluster local (Kind/Minikube)
- **tetragon/** — Configuration du DaemonSet Tetragon pour l'instrumentation du noyau
- **policies/** — Politiques de traçage (YAML) définissant les événements à capturer :
  - `trace-exec.yaml` — Capture les événements `execve` (exécution de processus)
  - `trace-tcp.yaml` — Capture les connexions TCP et réseau

Génère un flux JSON filtré et pertinent en temps réel.

### 3. src/ — Moteur d'Analyse Comportementale
**Cœur algorithmique du projet : transformation et détection.**

#### 📥 ingestion/ — Architecture des Données

Responsable de la **lecture et modélisation** du flux JSON Tetragon :

- **collector.py** — Collecte les événements en temps réel depuis Tetragon
- **graph_model.py** — Modélise les données en graphes comportementaux :
  - Nœuds : Pods, Processus, Fichiers, Connexions réseau
  - Arêtes : Relations entre entités (exécution, accès fichier, communication)
  - Utilise NetworkX ou Neo4j pour la persistance et les requêtes

#### 🔍 analysis/ — Détection d'Anomalies

Moteur intelligent de détection basé sur l'apprentissage comportemental :

- **baseline.py** — Phase d'apprentissage du comportement normal
  - Construit un profil de référence par application/pod
  - Enregistre les patterns usuels
  
- **detector.py** — Comparaison et détection en temps réel
  - Détecte les écarts au modèle de référence
  - Identifie les comportements suspects (ex: accès à `/etc/passwd`, connexions non autorisées)
  - Génère des alertes avec score de confiance

- **storage/** — Persistance des profils
  - Sauvegarde les baselines générées
  - Permet la comparaison historique

### 4. dashboard/ — Visualisation Temps Réel
**Interface utilisateur interactive pour le monitoring en temps réel :**

- **app.py** — Application Streamlit/Dash principale
- **utils.py** — Utilitaires de visualisation et formatage

Fonctionnalités :
- 📊 Visualisation du graphe comportemental en temps réel
- 🚨 Affichage des alertes et anomalies détectées
- 🔴 Mise en évidence des nœuds compromis
- 📈 Statistiques et tendances de sécurité
- 📋 Audit trail détaillé des événements

### 5. red_team/ — Validation & Tests de Sécurité
**Simulation et validation des scénarios d'attaque :**

- **scenario.md** — Description des scénarios d'attaque testés
- **attacks/**
  - `priv_escalation.sh` — Simulation d'escalade de privilèges
  - `reverse_shell.sh` — Simulation de reverse shell

Permet de :
- ✅ Valider la capture des comportements suspects
- 📊 Mesurer le taux de détection
- 🔧 Affiner les règles de détection
- 📝 Générer des rapports de test

---

## 🚀 Flux d'Exécution

```
┌─────────────────────────────────────────────────────────────┐
│  1. Événements Noyau (execve, tcp_connect, file_access)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  2. Tetragon (eBPF) → Traçage + Filtrage via Policies       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  3. Flux JSON → ingestion/collector.py                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  4. Modélisation Graphe (ingestion/graph_model.py)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌────────▼─────────┐
│ Baseline       │          │ Détection        │
│ (Phase Appren.)│          │ (Phase Runtime)  │
└────────────────┘          └────────┬─────────┘
        │                             │
        └──────────────┬──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  5. Dashboard → Visualisation & Alertes                     │
└──────────────────────────────────────────────────────────────┘
```

## 📋 Configuration Requise

- **OS** : Linux (support eBPF natif)
- **Orchestration** : Kubernetes (Kind, Minikube ou cluster production)
- **Dépendances Python** : voir [requirement.txt](requirement.txt)
- **eBPF Programs** : Tetragon (v1.0+)

## ⚡ Quick Start — Mise en route rapide

Suivez ces étapes pour configurer l'environnement de développement et lancer le tableau de bord.

1. Ouvrez un terminal et placez-vous dans la racine du projet :

```bash
cd Architectural-Blueprint-for-eBPF-Graph-Based-Intrusion-Detection
```

2. Lancez le script d'installation (choisissez l'une des options) :

```bash
bash setup.sh
```

3. Activez l'environnement virtuel :

```bash
source venv/bin/activate
```

4. Vérifiez rapidement l'installation :

```bash
python -c "import streamlit, networkx, pandas; print('✓ Setup OK')"
```

5. Démarrez le tableau de bord :

```bash
streamlit run dashboard/app.py
```

Remarques :
- Le fichier `.env` est généré automatiquement par le script et contient les variables de configuration (port du dashboard, chemins de stockage, etc.).
- Si `venv/`, `data/`, `models/` ou `logs/` existent localement et que vous voulez tout reprendre à zéro, supprimez `venv/` puis relancez le script d'installation.


## 📝 Documentation Supplémentaire

Consulter les fichiers de documentation dans `docs/` pour :
- L'architecture technique détaillée
- Les schémas algorithmiques
- Les spécifications Tetragon
- L'analyse d'état de l'art