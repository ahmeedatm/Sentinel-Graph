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

Moteur de détection basé sur le **fingerprinting comportemental par processus** (`comm`).
Aucun ML — les règles sont explicites et auditables.

- **baseline.py** — `BaselineLearner` : phase d'apprentissage du comportement normal
  - Consomme des snapshots `SystemGraph.get_graph_snapshot()` via `learn()`
  - Construit un profil par nom de processus (`comm`) :
    - `spawns` — processus enfants observés
    - `reads` — chemins de fichiers lus
    - `writes` — chemins de fichiers écrits
    - `connects` — destinations réseau `"ip:port"`
  - Persistance JSON via `save()` / `load()`

- **detector.py** — `AnomalyDetector` + dataclass `Alert` : détection en temps réel
  - Compare chaque arête d'un snapshot contre le profil baseline
  - Types d'alertes générées :

    | Type | Déclencheur | Sévérité |
    |------|-------------|----------|
    | `UNKNOWN_PROCESS` | `comm` absent du baseline | MEDIUM |
    | `UNEXPECTED_SPAWN` | processus enfant non vu | HIGH |
    | `UNEXPECTED_FILE_READ` | lecture non observée | HIGH si chemin sensible, sinon MEDIUM |
    | `UNEXPECTED_FILE_WRITE` | écriture non observée | HIGH si chemin sensible, sinon MEDIUM |
    | `UNEXPECTED_CONNECTION` | destination réseau non vue | HIGH |

  - Chemins toujours HIGH : `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/root/`, `/.ssh/`, `/etc/crontab`, `/proc/`

- **storage/** — Persistance des profils baseline (JSON)

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

- **OS** : Mac (avec Docker/Kind) ou Linux (support eBPF natif)
- **Orchestration** : Kubernetes (Kind) pour le test local
- **Dépendances Python** : voir `requirement.txt`
- **eBPF Agent** : Tetragon

## ⚡ Quick Start — Déploiement et Test Rapide

L'architecture nécessite de connecter votre environnement local Python avec le cluster Kubernetes contenant Tetragon.

### Étape 1 : Initialisation de l'Infrastructure (Une seule fois)
Si votre cluster n'est pas encore créé, lancez le script d'installation infrastructure. Cela construira le cluster `kind` et installera la chart Helm de Tetragon.

```bash
bash infra/tetragon/install.sh
```

### Étape 2 : Lancement Automatisé (La méthode Recommandée) ⭐
Pour éviter de manipuler 3 terminaux (un pour le port-forwarding, un pour Streamlit, un pour les tests), **un script tout-en-un a été créé**. 
Il lance le tunnel gRPC de K8s en arrière-plan et démarre Streamlit pour vous :

```bash
./start.sh
```
> 💡 *Note: Lorsque vous quitterez Streamlit (Ctrl+C), le script s'occupera de tuer proprement le tunnel de port-forwarding en arrière-plan.*

### Étape 3 : Simulation d'une attaque (Terminal Séparé)
Pendant que votre Dashboard tourne, ouvrez un nouveau terminal pour injecter du trafic dans le cluster et voir la magie opérer en temps réel !

1. Lancez un pod Alpine éphémère :
   ```bash
   kubectl run shell-test -it --rm --image=alpine -- sh
   ```
2. Installez `curl` (Témoin de création de processus/fichiers eBPF) :
   ```bash
   apk add curl
   ```
3. Générez des connexions TCP :
   ```bash
   curl https://google.com
   ```
4. Observez le dashboard Sentinel-Graph s'animer ! 🚀

### Méthode Manuelle (Configuration Historique)
Si vous souhaitez observer les composants séparément, divisez votre écran en 2 terminaux :
**Terminal A (Connexion K8s) :**
```bash
kubectl port-forward -n kube-system ds/tetragon 54321:54321
```
**Terminal B (Lancement applicatif) :**
```bash
streamlit run dashboard/app.py
```


## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture de code (cible ≥ 80 %)
pytest --cov=src --cov-report=term-missing

# Tests par module
pytest tests/test_baseline.py tests/test_detector.py -v   # analyse
pytest tests/test_graph_model.py tests/test_collector.py -v  # ingestion
```

Couverture actuelle : **91 %** (149 tests).

---

## 📝 Documentation Supplémentaire

Consulter les fichiers de documentation dans `docs/` pour :
- L'architecture technique détaillée
- Les schémas algorithmiques
- Les spécifications Tetragon
- L'analyse d'état de l'art