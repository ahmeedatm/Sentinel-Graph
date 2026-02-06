import { useState, useEffect } from "react";

// ─── CALENDAR (2 fév → 12 avril = 70 days, index 0..69) ───
const START = new Date(2026, 1, 2);
const TOTAL_DAYS = 70;

function dayIndex(month, day) {
  const d = new Date(2026, month - 1, day);
  return Math.round((d - START) / 86400000);
}

const WEEKS = [
  { label: "Sem 6", start: dayIndex(2,2),  end: dayIndex(2,9) },
  { label: "Sem 7", start: dayIndex(2,9),  end: dayIndex(2,16) },
  { label: "Sem 8", start: dayIndex(2,16), end: dayIndex(2,23) },
  { label: "Sem 9", start: dayIndex(2,23), end: dayIndex(3,2) },
  { label: "Sem 10", start: dayIndex(3,2),  end: dayIndex(3,9) },
  { label: "Sem 11", start: dayIndex(3,9),  end: dayIndex(3,16) },
  { label: "Sem 12", start: dayIndex(3,16), end: dayIndex(3,23) },
  { label: "Sem 13", start: dayIndex(3,23), end: dayIndex(3,30) },
  { label: "Sem 14", start: dayIndex(3,30), end: dayIndex(4,6) },
  { label: "Sem 15", start: dayIndex(4,6),  end: TOTAL_DAYS },
];

const MONTHS = [
  { label: "FÉVRIER", startDay: 0,               endDay: dayIndex(3,1) },
  { label: "MARS",    startDay: dayIndex(3,1),   endDay: dayIndex(4,1) },
  { label: "AVRIL",   startDay: dayIndex(4,1),   endDay: TOTAL_DAYS },
];

// ─── MILESTONES ───
const milestones = [
  { day: dayIndex(2,2),  label: "2 fév (PM) — Séance démarrage à distance",        type: "session" },
  { day: dayIndex(2,6),  label: "6 fév (PM) — Travail supervisé à distance",       type: "session" },
  { day: dayIndex(2,23), label: "23 fév — Deadline transfert CdC sur Moodle",      type: "deadline"},
  { day: dayIndex(2,24), label: "24 fév (PM) — Présentation CdC (10')",            type: "pres"    },
  { day: dayIndex(3,16), label: "16 mars (AM) — Séance supervisée présentiel",     type: "session" },
  { day: dayIndex(3,17), label: "17 mars (AM) — Séance supervisée présentiel",     type: "session" },
  { day: dayIndex(3,18), label: "18 mars (AM) — Séance supervisée présentiel",     type: "session" },
  { day: dayIndex(3,19), label: "19 mars (AM) — Séance supervisée présentiel",     type: "session" },
  { day: dayIndex(3,23), label: "23 mars (AM) — Séance supervisée distanciel",     type: "session" },
  { day: dayIndex(3,24), label: "24 mars — Remise rapport intermédiaire",          type: "deadline"},
  { day: dayIndex(3,25), label: "25 mars (AM) — Soutenance mi-parcours (30')",     type: "pres"    },
  { day: dayIndex(3,27), label: "27 mars (AM) — Séance supervisée",                type: "session" },
  { day: dayIndex(4,12), label: "12 avril — Remise rapport final + démo",          type: "deadline"},
];

// ─── TASKS ────────────────────────────────────────────
const tasks = [
  // ── ANTOINE - Infrastructure & eBPF ──
  {
    id:"An1", owner:"Antoine", phase:"Phase 1: Cadrage",
    task:"Participation séance de démarrage",
    desc:"2 fév PM : Présentation projet Tetragon. Compréhension objectifs. Distribution des rôles.",
    start: dayIndex(2,2),  end: dayIndex(2,3),
  },
  {
    id:"An2", owner:"Antoine", phase:"Phase 1: Cadrage",
    task:"État de l'art eBPF & Tetragon",
    desc:"Lecture articles [4][5][6] sur eBPF. Étude documentation Tetragon et Cilium. Compréhension architecture.",
    start: dayIndex(2,2),  end: dayIndex(2,16),
  },
  {
    id:"An3", owner:"Antoine", phase:"Phase 1: Cadrage",
    task:"Contribution au Cahier des Charges",
    desc:"Rédaction section infrastructure : déploiement K8s, installation Tetragon, configuration DaemonSet.",
    start: dayIndex(2,6),  end: dayIndex(2,15),
  },
  {
    id:"An4", owner:"Antoine", phase:"Phase 1: Cadrage",
    task:"Création diagramme de Gantt",
    desc:"Planification timeline du projet. Répartition tâches infrastructure. Export PDF professionnel.",
    start: dayIndex(2,10), end: dayIndex(2,20),
  },
  {
    id:"An5", owner:"Antoine", phase:"Phase 1: Cadrage",
    task:"Préparation présentation 24 fév",
    desc:"Slides architecture infrastructure K8s/Tetragon. Schéma déploiement. 2-3 min de présentation.",
    start: dayIndex(2,18), end: dayIndex(2,24),
  },
  {
    id:"An6", owner:"Antoine", phase:"Phase 1: Cadrage",
    task:"Présentation CdC 24 fév (2-3')",
    desc:"24 fév PM : Présentation architecture infrastructure. Déploiement Tetragon. Réponse aux questions.",
    start: dayIndex(2,24), end: dayIndex(2,25),
  },
  
  {
    id:"An7", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Setup environnement Kubernetes local",
    desc:"Installation Kind ou Minikube. Configuration cluster local. Tests connectivité pods.",
    start: dayIndex(2,20), end: dayIndex(3,2),
  },
  {
    id:"An8", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Installation Tetragon en DaemonSet",
    desc:"Déploiement Tetragon sur cluster. Configuration collect d'événements. Vérification logs.",
    start: dayIndex(3,1),  end: dayIndex(3,8),
  },
  {
    id:"An9", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Écriture TracingPolicies YAML",
    desc:"Création policies pour execve, tcp_connect, file operations. Filtrage événements pertinents.",
    start: dayIndex(3,5),  end: dayIndex(3,15),
  },
  {
    id:"An10", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Optimisation flux JSON",
    desc:"Configuration output JSON propre. Filtrage bruit. Export vers service Python d'Ahmed.",
    start: dayIndex(3,12), end: dayIndex(3,20),
  },
  {
    id:"An11", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Rédaction conception technique [RI]",
    desc:"Documentation architecture déployée. Choix techniques justifiés. Diagrammes infrastructure.",
    start: dayIndex(3,10), end: dayIndex(3,22),
  },
  {
    id:"An12", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Préparation soutenance mi-parcours",
    desc:"Slides démo infrastructure. Captures logs Tetragon. Présentation TracingPolicies. 7-8 min.",
    start: dayIndex(3,18), end: dayIndex(3,24),
  },
  {
    id:"An13", owner:"Antoine", phase:"Phase 2: Implémentation",
    task:"Soutenance 25 mars (7-8')",
    desc:"25 mars AM : Présentation infrastructure déployée. Démo Tetragon live. Réponse questions jury.",
    start: dayIndex(3,25), end: dayIndex(3,26),
  },
  
  {
    id:"An14", owner:"Antoine", phase:"Phase 3: Tests & Validation",
    task:"Tests de charge infrastructure",
    desc:"Vérification stabilité K8s sous charge. Monitoring ressources. Optimisation performances.",
    start: dayIndex(3,20), end: dayIndex(3,30),
  },
  {
    id:"An15", owner:"Antoine", phase:"Phase 3: Tests & Validation",
    task:"Validation intégration avec pipeline Python",
    desc:"Tests bout-en-bout avec script Ahmed. Vérification flux données. Debugging connectivité.",
    start: dayIndex(3,25), end: dayIndex(4,3),
  },
  {
    id:"An16", owner:"Antoine", phase:"Phase 3: Tests & Validation",
    task:"Documentation déploiement",
    desc:"Guide installation pas-à-pas. Scripts automatisation. Procédures troubleshooting.",
    start: dayIndex(3,27), end: dayIndex(4,8),
  },
  {
    id:"An17", owner:"Antoine", phase:"Phase 3: Tests & Validation",
    task:"Rédaction rapport final - partie infra",
    desc:"Compte-rendu déploiement. Résultats tests performance. Leçons apprises. Améliorations futures.",
    start: dayIndex(4,1),  end: dayIndex(4,10),
  },
  {
    id:"An18", owner:"Antoine", phase:"Phase 3: Tests & Validation",
    task:"Finalisation livrables + remise 12 avril",
    desc:"12 avril : Upload Moodle rapport final + scripts déploiement + vidéo démo infrastructure.",
    start: dayIndex(4,10), end: dayIndex(4,12),
  },

  // ── AHMED - Architecte de Données (Python/Graphes) ──
  {
    id:"Ah1", owner:"Ahmed", phase:"Phase 1: Cadrage",
    task:"Participation séance de démarrage",
    desc:"2 fév PM : Compréhension objectifs mapping graphes. Distribution rôles.",
    start: dayIndex(2,2),  end: dayIndex(2,3),
  },
  {
    id:"Ah2", owner:"Ahmed", phase:"Phase 1: Cadrage",
    task:"État de l'art graphes & observabilité",
    desc:"Étude NetworkX, Neo4j. Lectures sur graph-based security. Modélisation comportements systèmes.",
    start: dayIndex(2,2),  end: dayIndex(2,16),
  },
  {
    id:"Ah3", owner:"Ahmed", phase:"Phase 1: Cadrage",
    task:"Contribution CdC - section graphes",
    desc:"Rédaction section modélisation données. Définition nœuds/arêtes. Architecture pipeline ingestion.",
    start: dayIndex(2,6),  end: dayIndex(2,15),
  },
  {
    id:"Ah4", owner:"Ahmed", phase:"Phase 1: Cadrage",
    task:"Préparation présentation 24 fév",
    desc:"Slides architecture données. Schéma modèle graphe. Exemples nœuds/relations. 2-3 min.",
    start: dayIndex(2,18), end: dayIndex(2,24),
  },
  {
    id:"Ah5", owner:"Ahmed", phase:"Phase 1: Cadrage",
    task:"Présentation CdC 24 fév (2-3')",
    desc:"24 fév PM : Présentation modèle de données graphe. Architecture ingestion. Questions.",
    start: dayIndex(2,24), end: dayIndex(2,25),
  },
  
  {
    id:"Ah6", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"Développement script ingestion JSON",
    desc:"Création parser logs Tetragon. Lecture temps réel. Extraction événements pertinents.",
    start: dayIndex(2,20), end: dayIndex(3,5),
  },
  {
    id:"Ah7", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"Modélisation avec NetworkX",
    desc:"Implémentation classes nœuds (Pod, Process, File, IP). Création arêtes (SPAWNS, CONNECTS_TO, MODIFIES).",
    start: dayIndex(3,1),  end: dayIndex(3,12),
  },
  {
    id:"Ah8", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"API Python pour requêtes graphe",
    desc:"Développement API : get_graph_state(), find_neighbors(), query_paths(). Tests unitaires.",
    start: dayIndex(3,8),  end: dayIndex(3,18),
  },
  {
    id:"Ah9", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"Intégration avec flux Tetragon (Antoine)",
    desc:"Connection au flux JSON d'Antoine. Tests bout-en-bout. Debugging format données.",
    start: dayIndex(3,12), end: dayIndex(3,20),
  },
  {
    id:"Ah10", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"Rédaction conception technique [RI]",
    desc:"Documentation architecture pipeline. Modèle données détaillé. Choix NetworkX vs Neo4j justifiés.",
    start: dayIndex(3,10), end: dayIndex(3,22),
  },
  {
    id:"Ah11", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"Préparation soutenance mi-parcours",
    desc:"Slides démo pipeline ingestion. Visualisation graphe exemple. Code samples. 7-8 min.",
    start: dayIndex(3,18), end: dayIndex(3,24),
  },
  {
    id:"Ah12", owner:"Ahmed", phase:"Phase 2: Implémentation",
    task:"Soutenance 25 mars (7-8')",
    desc:"25 mars AM : Présentation pipeline données. Démo graphe live. Questions jury.",
    start: dayIndex(3,25), end: dayIndex(3,26),
  },
  
  {
    id:"Ah13", owner:"Ahmed", phase:"Phase 3: Tests & Validation",
    task:"Optimisation performances graphes",
    desc:"Profiling mémoire. Optimisation requêtes. Gestion graphes large échelle. Benchmarks.",
    start: dayIndex(3,20), end: dayIndex(4,2),
  },
  {
    id:"Ah14", owner:"Ahmed", phase:"Phase 3: Tests & Validation",
    task:"Intégration avec moteur détection (Jonathan)",
    desc:"Export format graphe pour analyse anomalies. API commune. Tests intégration.",
    start: dayIndex(3,25), end: dayIndex(4,5),
  },
  {
    id:"Ah15", owner:"Ahmed", phase:"Phase 3: Tests & Validation",
    task:"Tests robustesse & edge cases",
    desc:"Tests données corrompues. Gestion événements manquants. Récupération erreurs.",
    start: dayIndex(3,27), end: dayIndex(4,6),
  },
  {
    id:"Ah16", owner:"Ahmed", phase:"Phase 3: Tests & Validation",
    task:"Documentation API Python",
    desc:"Docstrings complètes. Guide utilisation API. Exemples d'usage. README développeur.",
    start: dayIndex(4,1),  end: dayIndex(4,8),
  },
  {
    id:"Ah17", owner:"Ahmed", phase:"Phase 3: Tests & Validation",
    task:"Rédaction rapport final - partie données",
    desc:"Architecture pipeline finalisée. Résultats benchmarks. Défis rencontrés. Solutions apportées.",
    start: dayIndex(4,2),  end: dayIndex(4,10),
  },
  {
    id:"Ah18", owner:"Ahmed", phase:"Phase 3: Tests & Validation",
    task:"Finalisation livrables + remise 12 avril",
    desc:"12 avril : Upload code Python + tests + documentation API + vidéo démo pipeline.",
    start: dayIndex(4,10), end: dayIndex(4,12),
  },

  // ── JÉRÉMY - Red Team & Visualisation ──
  {
    id:"J1", owner:"Jérémy", phase:"Phase 1: Cadrage",
    task:"Participation séance de démarrage",
    desc:"2 fév PM : Compréhension objectifs Red Team. Distribution rôles sécurité.",
    start: dayIndex(2,2),  end: dayIndex(2,3),
  },
  {
    id:"J2", owner:"Jérémy", phase:"Phase 1: Cadrage",
    task:"État de l'art attaques conteneurs",
    desc:"Étude MITRE ATT&CK containers. Techniques escape, privilege escalation. CVEs récents.",
    start: dayIndex(2,2),  end: dayIndex(2,16),
  },
  {
    id:"J3", owner:"Jérémy", phase:"Phase 1: Cadrage",
    task:"Contribution CdC - scénarios d'attaque",
    desc:"Définition scénarios tests : reverse shell, privesc, data exfiltration. Métriques succès.",
    start: dayIndex(2,6),  end: dayIndex(2,15),
  },
  {
    id:"J4", owner:"Jérémy", phase:"Phase 1: Cadrage",
    task:"Préparation présentation 24 fév",
    desc:"Slides scénarios attaque planifiés. Architecture visualisation. Outils (Streamlit/Dash). 2-3 min.",
    start: dayIndex(2,18), end: dayIndex(2,24),
  },
  {
    id:"J5", owner:"Jérémy", phase:"Phase 1: Cadrage",
    task:"Présentation CdC 24 fév (2-3')",
    desc:"24 fév PM : Présentation approche Red Team. Scénarios d'attaque. Dashboard visualisation.",
    start: dayIndex(2,24), end: dayIndex(2,25),
  },
  
  {
    id:"J6", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Développement scripts d'attaque",
    desc:"Création exploits : reverse shell, container escape, privilege escalation. Tests isolation.",
    start: dayIndex(2,20), end: dayIndex(3,10),
  },
  {
    id:"J7", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Prototype dashboard Streamlit",
    desc:"Interface visualisation graphes temps réel. Intégration API Ahmed. Affichage événements suspects.",
    start: dayIndex(3,1),  end: dayIndex(3,15),
  },
  {
    id:"J8", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Intégration visualisation graphes",
    desc:"Affichage graphes NetworkX dans Streamlit. Coloration nœuds suspects (rouge). Navigation interactive.",
    start: dayIndex(3,10), end: dayIndex(3,20),
  },
  {
    id:"J9", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Tests initiaux attaques sur testbed",
    desc:"Exécution scripts d'attaque sur env d'Antoine. Vérification détection. Collecte résultats.",
    start: dayIndex(3,15), end: dayIndex(3,23),
  },
  {
    id:"J10", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Rédaction conception technique [RI]",
    desc:"Documentation suite de tests. Architecture dashboard. Scénarios d'attaque détaillés.",
    start: dayIndex(3,10), end: dayIndex(3,22),
  },
  {
    id:"J11", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Préparation soutenance mi-parcours",
    desc:"Slides démo attaques. Captures dashboard. Vidéo reverse shell détecté en temps réel. 7-8 min.",
    start: dayIndex(3,18), end: dayIndex(3,24),
  },
  {
    id:"J12", owner:"Jérémy", phase:"Phase 2: Implémentation",
    task:"Soutenance 25 mars (7-8')",
    desc:"25 mars AM : Présentation Red Team + dashboard. Démo attaque live. Questions jury.",
    start: dayIndex(3,25), end: dayIndex(3,26),
  },
  
  {
    id:"J13", owner:"Jérémy", phase:"Phase 3: Tests & Validation",
    task:"Campagne complète tests d'intrusion",
    desc:"Exécution systématique tous scénarios. Mesure taux détection. Identification faux positifs/négatifs.",
    start: dayIndex(3,20), end: dayIndex(4,5),
  },
  {
    id:"J14", owner:"Jérémy", phase:"Phase 3: Tests & Validation",
    task:"Amélioration dashboard final",
    desc:"Ajout alertes temps réel. Graphiques statistiques détection. Export rapports PDF.",
    start: dayIndex(3,25), end: dayIndex(4,6),
  },
  {
    id:"J15", owner:"Jérémy", phase:"Phase 3: Tests & Validation",
    task:"Documentation suite de tests",
    desc:"Guide reproduction attaques. Procédures test. Résultats attendus vs obtenus.",
    start: dayIndex(3,27), end: dayIndex(4,8),
  },
  {
    id:"J16", owner:"Jérémy", phase:"Phase 3: Tests & Validation",
    task:"Rédaction rapport final - partie Red Team",
    desc:"Campagne tests détaillée. Résultats détection par type d'attaque. Recommandations amélioration.",
    start: dayIndex(4,2),  end: dayIndex(4,10),
  },
  {
    id:"J17", owner:"Jérémy", phase:"Phase 3: Tests & Validation",
    task:"Finalisation livrables + remise 12 avril",
    desc:"12 avril : Upload scripts attaque + dashboard + vidéo démos + rapport tests.",
    start: dayIndex(4,10), end: dayIndex(4,12),
  },

  // ── JONATHAN - Chef de Projet & Détection Algorithmique ──
  {
    id:"Jo1", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"Coordination séance de démarrage",
    desc:"2 fév PM : Animation séance. Présentation vision projet. Répartition rôles finalisée.",
    start: dayIndex(2,2),  end: dayIndex(2,3),
  },
  {
    id:"Jo2", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"Coordination travail supervisé 6 fév",
    desc:"6 fév PM : Finalisation CdC. Plan développement. Diagramme Gantt. Coordination équipe.",
    start: dayIndex(2,6),  end: dayIndex(2,7),
  },
  {
    id:"Jo3", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"État de l'art détection anomalies",
    desc:"Étude algorithmes détection anomalies. Graph-based anomaly detection. Baseline behavior modeling.",
    start: dayIndex(2,2),  end: dayIndex(2,16),
  },
  {
    id:"Jo4", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"Rédaction CdC complet",
    desc:"Intégration sections équipe. Structuration document. Mise en page professionnelle. Relecture finale.",
    start: dayIndex(2,6),  end: dayIndex(2,20),
  },
  {
    id:"Jo5", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"Transfert CdC sur Moodle",
    desc:"23 fév : Upload CdC finalisé PDF. Vérification conformité template. Validation liens.",
    start: dayIndex(2,20), end: dayIndex(2,23),
  },
  {
    id:"Jo6", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"Coordination présentation 24 fév",
    desc:"Coordination slides équipe. Répétition timing (10' total). Introduction/conclusion projet.",
    start: dayIndex(2,18), end: dayIndex(2,24),
  },
  {
    id:"Jo7", owner:"Jonathan", phase:"Phase 1: Cadrage",
    task:"Présentation CdC 24 fév (intro + conclusion)",
    desc:"24 fév PM : Introduction contexte Tetragon. Coordination présentations. Conclusion objectifs. 2 min.",
    start: dayIndex(2,24), end: dayIndex(2,25),
  },
  
  {
    id:"Jo8", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Conception algorithme détection",
    desc:"Design moteur baseline learning. Stratégie comparaison graphes. Métriques de similarité.",
    start: dayIndex(2,20), end: dayIndex(3,8),
  },
  {
    id:"Jo9", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Implémentation baseline learning",
    desc:"Enregistrement phase apprentissage comportement normal. Sérialisation graphe référence (JSON/Pickle).",
    start: dayIndex(3,1),  end: dayIndex(3,12),
  },
  {
    id:"Jo10", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Développement moteur de détection",
    desc:"Algorithme comparaison temps réel vs baseline. Règles détection (nouveaux nœuds, arêtes suspectes). Alerting.",
    start: dayIndex(3,8),  end: dayIndex(3,20),
  },
  {
    id:"Jo11", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Intégration avec graphes (Ahmed)",
    desc:"Connection API graphes d'Ahmed. Tests détection sur données réelles. Tuning seuils.",
    start: dayIndex(3,15), end: dayIndex(3,23),
  },
  {
    id:"Jo12", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Rédaction rapport intermédiaire",
    desc:"Consolidation sections équipe. Rédaction section détection. Graphiques. Mise en page finale.",
    start: dayIndex(3,15), end: dayIndex(3,23),
  },
  {
    id:"Jo13", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Remise RI sur Moodle",
    desc:"24 mars : Upload rapport intermédiaire PDF. Vérification structure conforme template.",
    start: dayIndex(3,23), end: dayIndex(3,24),
  },
  {
    id:"Jo14", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Coordination soutenance mi-parcours",
    desc:"Coordination slides équipe (30' total). Répétition. Préparation réponses questions jury.",
    start: dayIndex(3,18), end: dayIndex(3,24),
  },
  {
    id:"Jo15", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Transfert présentation sur Moodle",
    desc:"Upload slides/vidéo avant 25 mars. Format PDF + MP4 si nécessaire.",
    start: dayIndex(3,24), end: dayIndex(3,25),
  },
  {
    id:"Jo16", owner:"Jonathan", phase:"Phase 2: Implémentation",
    task:"Soutenance 25 mars (intro + détection 7-8')",
    desc:"25 mars AM : Introduction projet. Présentation moteur détection. Coordination équipe. Questions jury.",
    start: dayIndex(3,25), end: dayIndex(3,26),
  },
  
  {
    id:"Jo17", owner:"Jonathan", phase:"Phase 3: Tests & Validation",
    task:"Validation détection sur scénarios Jérémy",
    desc:"Tests détection sur attaques réelles. Mesure précision/rappel. Analyse faux positifs.",
    start: dayIndex(3,20), end: dayIndex(4,3),
  },
  {
    id:"Jo18", owner:"Jonathan", phase:"Phase 3: Tests & Validation",
    task:"Optimisation algorithme détection",
    desc:"Amélioration taux détection. Réduction faux positifs. Tuning paramètres. Benchmarks.",
    start: dayIndex(3,25), end: dayIndex(4,5),
  },
  {
    id:"Jo19", owner:"Jonathan", phase:"Phase 3: Tests & Validation",
    task:"Identification attaques non détectées",
    desc:"Analyse attaques zero-day potentielles. Techniques d'évasion. Recommandations améliorations futures.",
    start: dayIndex(4,1),  end: dayIndex(4,8),
  },
  {
    id:"Jo20", owner:"Jonathan", phase:"Phase 3: Tests & Validation",
    task:"Coordination rapport final",
    desc:"Consolidation sections équipe. Rédaction synthèse générale. Conclusions. Perspectives.",
    start: dayIndex(4,2),  end: dayIndex(4,10),
  },
  {
    id:"Jo21", owner:"Jonathan", phase:"Phase 3: Tests & Validation",
    task:"Coordination vidéo démo finale",
    desc:"Scénario démo complète bout-en-bout. Montage vidéo. Commentaires audio. Export HD.",
    start: dayIndex(4,5),  end: dayIndex(4,11),
  },
  {
    id:"Jo22", owner:"Jonathan", phase:"Phase 3: Tests & Validation",
    task:"Remise finale 12 avril",
    desc:"12 avril : Upload rapport final PDF + code + vidéo démo complète + fichiers annexes.",
    start: dayIndex(4,11), end: dayIndex(4,12),
  },
];

// ─── COLOURS ──────────────────────────────────────────
const C = {
  jonathan: { bar:"#8b5cf6", dark:"#6d28d9", glow:"rgba(139,92,246,.4)", bg:"#f3e8ff" },
  ahmed:    { bar:"#10b981", dark:"#059669", glow:"rgba(16,185,129,.4)", bg:"#d1fae5" },
  jérémy:   { bar:"#ef4444", dark:"#dc2626", glow:"rgba(239,68,68,.4)",  bg:"#fee2e2" },
  antoine:  { bar:"#38bdf8", dark:"#0369a1", glow:"rgba(56,189,248,.4)", bg:"#e0f2fe" },
};
const PHASE_C = {
  "Phase 1: Cadrage":         "#8b5cf6",
  "Phase 2: Implémentation":  "#3b82f6",
  "Phase 3: Tests & Validation": "#10b981",
};
const MS_C = { session:"#64748b", pres:"#7c3aed", deadline:"#ef4444" };

const pct = d => `${(d / TOTAL_DAYS) * 100}%`;
const fmtDate = dayOff => {
  const d = new Date(START);
  d.setDate(d.getDate() + dayOff);
  return `${d.getDate()} ${["jan","fév","mar","avr"][d.getMonth()]}`;
};

export default function GanttTetragon() {
  const [sel, setSel]             = useState(null);
  const [filter, setFilter]       = useState("all");
  const [now, setNow]             = useState(null);
  const [expandedOwner, setExpandedOwner] = useState({ Jonathan: true, Ahmed: true, Jérémy: true, Antoine: true });
  const [expandedPhase, setExpandedPhase] = useState({});
  const [taskEdits, setTaskEdits]  = useState({});
  const [editingId, setEditingId]  = useState(null);

  useEffect(() => {
    const today = new Date();
    const idx = Math.round((today - START) / 86400000);
    if (idx >= 0 && idx <= TOTAL_DAYS) setNow(idx);
  }, []);

  const toggleOwner = (owner) => {
    setExpandedOwner(prev => ({ ...prev, [owner]: !prev[owner] }));
  };

  const togglePhase = (owner, phase) => {
    const key = `${owner}_${phase}`;
    setExpandedPhase(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleTaskCompletion = (taskId) => {
    setTaskEdits(prev => ({
      ...prev,
      [taskId]: { ...(prev[taskId] || {}), completed: !prev[taskId]?.completed }
    }));
  };

  const updateTaskDuration = (taskId, newStart, newEnd) => {
    if (newStart >= 0 && newEnd <= TOTAL_DAYS && newStart < newEnd) {
      setTaskEdits(prev => ({
        ...prev,
        [taskId]: { ...(prev[taskId] || {}), start: newStart, end: newEnd }
      }));
    }
  };

  const getTaskData = (task) => {
    const edits = taskEdits[task.id];
    return {
      start: edits?.start !== undefined ? edits.start : task.start,
      end: edits?.end !== undefined ? edits.end : task.end,
      completed: edits?.completed || false
    };
  };

  const LABEL_WIDTH = 280;

  const exportToPDF = () => {
    const element = document.getElementById("gantt-container");
    
    const contentWidth = element.scrollWidth;
    const contentHeight = element.scrollHeight;
    
    const pxToMm = 0.264583;
    const pdfWidth = Math.max(297, contentWidth * pxToMm);
    const pdfHeight = Math.max(210, contentHeight * pxToMm);
    
    const opt = {
      margin: [5, 5, 5, 5],
      filename: "gantt_Tetragon_USRS7N.pdf",
      image: { type: "jpeg", quality: 0.95 },
      html2canvas: { 
        scale: 2, 
        useCORS: true,
        scrollX: 0,
        scrollY: 0,
        windowWidth: contentWidth,
        windowHeight: contentHeight,
        width: contentWidth,
        height: contentHeight
      },
      jsPDF: { 
        orientation: pdfWidth > pdfHeight ? "landscape" : "portrait", 
        unit: "mm", 
        format: [pdfWidth, pdfHeight]
      }
    };
    
    import("html2pdf.js").then(html2pdf => {
      html2pdf.default().set(opt).from(element).save();
    }).catch(() => {
      alert("Export PDF : installez 'html2pdf.js' via npm install html2pdf.js");
    });
  };

  const filtered = tasks.filter(t => {
    const matches = filter === "all" || t.owner.toLowerCase() === filter;
    const duration = (t.end - t.start);
    return matches && duration >= 0;
  });

  return (
      <div style={{
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        background: "#f8fafc",
        color: "#1e293b",
        minHeight: "100vh",
        width: "100vw",
        margin: "0",
        padding: "20px",
        boxSizing: "border-box",
        overflowX: "auto",
        display: "flex",
        flexDirection: "column",
      }} id="gantt-container">
      
      <div style={{ display:"flex", alignItems:"center", gap:20, marginBottom:16, justifyContent:"space-between" }}>
        <div style={{ flex:1 }}>
          <h1 style={{
            margin:0, fontSize:20, fontWeight:700, letterSpacing:"-.3px",
            color:"#6d28d9"
          }}>Projet Tetragon — Observabilité & Détection Zero-Day</h1>
          <p style={{ margin:"3px 0 0", fontSize:10.5, color:"#64748b" }}>
            USRS7N - Projets avancés en IoT et cybersécurité · eBPF, Graphes de comportement · Master 2025-2026
          </p>
        </div>
        
        <div style={{ display:"flex", flexDirection:"column", gap:8, minWidth:160 }}>
          <button onClick={exportToPDF} style={{
            background:"linear-gradient(135deg,#6d28d9,#5b21b6)",
            border:"1.5px solid #6d28d9",
            color:"#fff",
            borderRadius:8,
            padding:"7px 16px",
            fontSize:11,
            fontWeight:600,
            cursor:"pointer",
            transition:"all .2s",
            boxShadow:"0 2px 8px rgba(109,40,217,.3)",
            whiteSpace:"nowrap"
          }}
            onMouseEnter={e => e.target.style.boxShadow = "0 4px 16px rgba(109,40,217,.5)"}
            onMouseLeave={e => e.target.style.boxShadow = "0 2px 8px rgba(109,40,217,.3)"}
          >
            📥 Export PDF
          </button>
        </div>
      </div>

      <div style={{ display:"flex", justifyContent:"center", gap:8, marginBottom:10, flexWrap:"wrap", alignItems:"center" }}>
        {["all","jonathan","ahmed","jérémy","antoine"].map(f => {
          const active = filter === f;
          const accent = f==="jonathan" ? C.jonathan.bar : f==="ahmed" ? C.ahmed.bar : f==="jérémy" ? C.jérémy.bar : f==="antoine" ? C.antoine.bar : "#94a3b8";
          return (
            <button key={f} onClick={()=>setFilter(f)} style={{
              background: active ? (f==="all"?"#cbd5e1":f==="jonathan"?"#f3e8ff":f==="ahmed"?"#d1fae5":f==="jérémy"?"#fee2e2":"#e0f2fe") : "#f1f5f9",
              border:`1.5px solid ${active ? accent : "#cbd5e1"}`,
              color: active?"#1e293b":"#64748b",
              borderRadius:16, padding:"4px 15px", fontSize:11.5,
              fontWeight:600, cursor:"pointer", letterSpacing:.5, transition:"all .17s",
            }}>
              {f==="all"?"Tous":f[0].toUpperCase()+f.slice(1)}
            </button>
          );
        })}
      </div>

      <div style={{ display:"flex", justifyContent:"center", gap:18, marginBottom:6, flexWrap:"wrap" }}>
        {Object.entries(PHASE_C).map(([ph,c])=>(
          <div key={ph} style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:9,height:9,borderRadius:2,background:c }}/>
            <span style={{ fontSize:10, color:"#64748b" }}>{ph}</span>
          </div>
        ))}
      </div>
      <div style={{ display:"flex", justifyContent:"center", gap:16, marginBottom:14 }}>
        {[["session","Séance supervisée"],["pres","Présentation"],["deadline","Deadline"]].map(([t,l])=>(
          <div key={t} style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:9, height:9, background:MS_C[t], borderRadius: t==="deadline"?"2px":"50%", transform: t==="pres"?"rotate(45deg)":"none" }}/>
            <span style={{ fontSize:10, color:"#64748b" }}>{l}</span>
          </div>
        ))}
      </div>

      <div style={{ flex: 1 }}>
      <div style={{
        background:"#ffffff",
        borderRadius:12,
        border:"1px solid #e2e8f0",
        boxShadow:"0 4px 24px rgba(0,0,0,.08)",
        width: "100%",
        overflowX: "auto",
        display: "flex",
        flexDirection: "column",
      }}>

        <div style={{ display:"flex" }}>
          <div style={{ width:LABEL_WIDTH, minWidth:LABEL_WIDTH, background:"#f1f5f9", borderRight:"1px solid #e2e8f0" }}/>
          <div style={{ flex:1, display:"flex" }}>
            {MONTHS.map(m=>(
              <div key={m.label} style={{
                width:`${((m.endDay-m.startDay)/TOTAL_DAYS)*100}%`,
                background:"#f1f5f9", textAlign:"center", padding:"5px 0",
                fontWeight:700, fontSize:10.5, letterSpacing:2, color:"#475569",
                borderRight:"1px solid #e2e8f0",
              }}>{m.label}</div>
            ))}
          </div>
        </div>

        <div style={{ display:"flex", borderBottom:"1px solid #e2e8f0" }}>
          <div style={{ width:LABEL_WIDTH, minWidth:LABEL_WIDTH, background:"#f1f5f9", padding:"3px 10px", fontSize:9.5, color:"#64748b", borderRight:"1px solid #e2e8f0", fontWeight:600, boxSizing:"border-box" }}>
            TÂCHE
          </div>
          <div style={{ flex:1, display:"flex" }}>
            {WEEKS.map((w,i)=>(
              <div key={i} style={{
                width:`${((w.end-w.start)/TOTAL_DAYS)*100}%`,
                background:"#f1f5f9", textAlign:"center", padding:"3px 0",
                fontSize:9.5, color:"#64748b", borderRight:"1px solid #e2e8f0",
                boxSizing:"border-box",
              }}>{w.label}</div>
            ))}
          </div>
        </div>

        <div style={{ display:"flex", borderBottom:"1px solid #e2e8f0" }}>
          <div style={{ width:LABEL_WIDTH, minWidth:LABEL_WIDTH, background:"#f1f5f9", padding:"2px 10px", fontSize:8.5, color:"#94a3b8", borderRight:"1px solid #e2e8f0", fontWeight:500, boxSizing:"border-box" }}>
            JOURS
          </div>
          <div style={{ flex:1, display:"flex", position:"relative" }}>
            {Array.from({length:TOTAL_DAYS}, (_, i) => {
              const d = new Date(START);
              d.setDate(d.getDate() + i);
              const dayNum = d.getDate();
              const isWeekend = d.getDay() === 0 || d.getDay() === 6;
              
              return (
                <div key={i} style={{
                  flex:`0 0 ${(1/TOTAL_DAYS)*100}%`,
                  textAlign:"left", padding:"1px 3px",
                  fontSize:7.5, color: isWeekend ? "#cbd5e1" : "#94a3b8",
                  background: isWeekend ? "#f8fafc" : "#ffffff",
                  borderRight:"1px solid #e2e8f0",
                  fontWeight:500,
                  boxSizing:"border-box",
                }}>{dayNum}</div>
              );
            })}
          </div>
        </div>

        {["Jonathan","Ahmed","Jérémy","Antoine"].map(owner => {
          const ownerTasks = filtered.filter(t=>t.owner===owner);
          if (!ownerTasks.length) return null;
          const c = C[owner.toLowerCase()];
          const isOwnerExpanded = expandedOwner[owner];
          
          const phases = ["Phase 1: Cadrage", "Phase 2: Implémentation", "Phase 3: Tests & Validation"];
          const tasksByPhase = {};
          phases.forEach(p => {
            tasksByPhase[p] = ownerTasks.filter(t => t.phase === p);
          });

          return (
            <div key={owner}>
              <div 
                style={{
                  display:"flex", alignItems:"center", gap:8,
                  background:`${c.dark}08`,
                  borderTop:`1px solid ${c.dark}22`,
                  borderBottom: isOwnerExpanded ? `1px solid ${c.dark}22` : "none",
                  padding:"8px 10px",
                  cursor:"pointer",
                  transition:"all .2s",
                }}
                onClick={() => toggleOwner(owner)}
              >
                <span style={{ fontSize:14, color:c.dark, fontWeight:700 }}>
                  {isOwnerExpanded ? "▼" : "▶"}
                </span>
                <div style={{ width:10, height:10, borderRadius:"50%", background:c.bar, boxShadow:`0 0 7px ${c.glow}` }}/>
                <span style={{ fontSize:12, fontWeight:700, color:c.dark, letterSpacing:1.4, flex:1 }}>
                  {owner.toUpperCase()}
                </span>
                <span style={{ fontSize:10, color:"#64748b" }}>
                  ({ownerTasks.length} tâches)
                </span>
              </div>

              {isOwnerExpanded && phases.map((phase, phaseIdx) => {
                const phaseTasks = tasksByPhase[phase];
                if (!phaseTasks.length) return null;
                
                const isPhaseExpanded = expandedPhase[`${owner}_${phase}`] !== false;
                
                return (
                  <div key={phase}>
                    <div 
                      style={{
                        display:"flex", alignItems:"center", gap:6,
                        background:`${c.dark}05`,
                        borderBottom:`1px solid ${c.dark}15`,
                        padding:"5px 10px 5px 30px",
                        cursor:"pointer",
                        transition:"all .2s",
                      }}
                      onClick={() => togglePhase(owner, phase)}
                    >
                      <span style={{ fontSize:11, color:c.dark, fontWeight:700 }}>
                        {isPhaseExpanded ? "▼" : "▶"}
                      </span>
                      <div style={{ width:6, height:6, borderRadius:1.5, background:PHASE_C[phase] }}/>
                      <span style={{ fontSize:10.5, fontWeight:600, color:"#1e293b" }}>
                        {phase}
                      </span>
                      <span style={{ fontSize:9.5, color:"#64748b", marginLeft:"auto" }}>
                        ({phaseTasks.length})
                      </span>
                    </div>

                    {isPhaseExpanded && phaseTasks.map((t, idx) => {
                      const isOpen = sel === t.id;
                      const taskData = getTaskData(t);
                      const isEditing = editingId === t.id;
                      
                      return (
                        <div key={t.id} style={{
                          display:"flex",
                          borderBottom:"1px solid #e2e8f0",
                          background: taskData.completed ? "#f8fafc" : (idx%2===0 ? "#ffffff" : "#f8fafc"),
                          opacity: taskData.completed ? 0.6 : 1,
                        }}>
                          <div style={{
                            width:LABEL_WIDTH, minWidth:LABEL_WIDTH, maxWidth:LABEL_WIDTH,
                            padding:"8px 10px",
                            paddingLeft:"50px",
                            borderRight:"1px solid #e2e8f0",
                            cursor:"pointer",
                            display:"flex", gap:7, alignItems:"flex-start",
                            boxSizing: "border-box",
                            overflow: "hidden",
                          }}
                            onClick={()=>setEditingId(isEditing ? null : t.id)}
                          >
                            <input 
                              type="checkbox"
                              checked={taskData.completed}
                              onChange={() => toggleTaskCompletion(t.id)}
                              style={{
                                width:16, height:16, cursor:"pointer", marginTop:3,
                                accentColor:"#6d28d9", flexShrink:0
                              }}
                              onClick={e => e.stopPropagation()}
                            />
                            
                            <div style={{ flex:1, minWidth:0 }}>
                              <div style={{ 
                                fontSize:11.5, fontWeight:600, color:"#1e293b", lineHeight:1.35,
                                textDecoration: taskData.completed ? "line-through" : "none",
                                color: taskData.completed ? "#94a3b8" : "#1e293b",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                              }}>{t.task}</div>
                              
                              {!isEditing && (
                                <div style={{ fontSize:9.5, color:"#64748b", marginTop:2, cursor:"pointer", whiteSpace:"nowrap" }}>
                                  {taskData.end - taskData.start}j
                                </div>
                              )}
                              
                              {isEditing && (
                                <div style={{ fontSize:9.5, marginTop:4, display:"flex", gap:4, alignItems:"center", flexWrap:"wrap" }}>
                                  <label style={{ color:"#64748b", fontWeight:600 }}>Début: {fmtDate(taskData.start)}</label>
                                  <input 
                                    type="number" 
                                    value={taskData.start}
                                    onChange={e => updateTaskDuration(t.id, parseInt(e.target.value), taskData.end)}
                                    style={{
                                      width:45, padding:"3px 6px", fontSize:9.5,
                                      background:"#f1f5f9", color:"#1e293b", border:"1px solid #cbd5e1",
                                      borderRadius:3
                                    }}
                                  />
                                  <label style={{ color:"#64748b", fontWeight:600 }}>Fin: {fmtDate(taskData.end)}</label>
                                  <input 
                                    type="number" 
                                    value={taskData.end}
                                    onChange={e => updateTaskDuration(t.id, taskData.start, parseInt(e.target.value))}
                                    style={{
                                      width:45, padding:"3px 6px", fontSize:9.5,
                                      background:"#f1f5f9", color:"#1e293b", border:"1px solid #cbd5e1",
                                      borderRadius:3
                                    }}
                                  />
                                  <span style={{ color:"#94a3b8", fontSize:8.5, fontWeight:600 }}>
                                    ({taskData.end - taskData.start}j)
                                  </span>
                                  <button 
                                    onClick={() => setEditingId(null)}
                                    style={{
                                      background:"#6d28d9", color:"#fff", border:"none",
                                      padding:"3px 10px", borderRadius:3, fontSize:9, cursor:"pointer",
                                      fontWeight:600
                                    }}
                                  >✓</button>
                                </div>
                              )}
                              
                              {isOpen && !isEditing && (
                                <div style={{
                                  fontSize:10.5, color:"#64748b", marginTop:5,
                                  borderTop:"1px solid #e2e8f0", paddingTop:5,
                                  lineHeight:1.45, maxWidth:216,
                                }}>{t.desc}</div>
                              )}
                            </div>
                          </div>

                          <div style={{ flex:1, position:"relative", minHeight:44, display:"flex", alignItems:"center" }}
                            onMouseEnter={()=>setSel(t.id)}
                            onMouseLeave={()=>setSel(null)}
                          >
                            {WEEKS.map((w,i)=>(
                              <div key={i} style={{ position:"absolute", left:pct(w.start), top:0, bottom:0, width:1, background:"#e2e8f0" }}/>
                            ))}
                            {now !== null && (
                              <div style={{
                                position:"absolute", left:pct(now), top:0, bottom:0,
                                width:2, background:"#ef4444", zIndex:3,
                                boxShadow:"0 0 5px #ef444488",
                              }}/>
                            )}
                            <div style={{
                              position:"absolute",
                              left:pct(taskData.start),
                              width:`${((taskData.end - taskData.start)/TOTAL_DAYS)*100}%`,
                              height:26,
                              top:"50%", transform:"translateY(-50%)",
                              background: taskData.completed ? `linear-gradient(90deg,${c.dark}44,${c.dark}22)` : `linear-gradient(90deg,${c.bar},${c.dark})`,
                              borderRadius:5,
                              boxShadow: isOpen ? `0 0 14px ${c.glow}` : "0 2px 4px rgba(0,0,0,.08)",
                              transition:"box-shadow .2s, background .2s",
                              zIndex:1,
                              display:"flex", alignItems:"center", justifyContent:"center",
                              border: taskData.completed ? `1px solid ${c.dark}44` : "none",
                            }}
                              onClick={()=>setSel(isOpen?null:t.id)}
                            >
                              <span style={{ 
                                fontSize:10, fontWeight:700, 
                                color: taskData.completed ? c.bar : "#fff", 
                                textShadow:"0 1px 2px rgba(0,0,0,.4)"
                              }}>
                                {taskData.completed ? "✓" : `${taskData.end - taskData.start}j`}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          );
        })}

        <div style={{ display:"flex", borderTop:"2px solid #e2e8f0", background:"#f1f5f9" }}>
          <div style={{
            width:LABEL_WIDTH, minWidth:LABEL_WIDTH,
            padding:"8px 10px",
            fontSize:11, fontWeight:700, color:"#6d28d9",
            borderRight:"1px solid #e2e8f0",
            display:"flex", alignItems:"center", gap:6,
          }}>
            <span style={{ fontSize:13 }}>◆</span> Jalons & Dates clés
          </div>
          <div style={{ flex:1, position:"relative", height:56 }}>
            {WEEKS.map((w,i)=>(
              <div key={i} style={{ position:"absolute", left:pct(w.start), top:0, bottom:0, width:1, background:"#e2e8f0" }}/>
            ))}
            {now !== null && (
              <div style={{
                position:"absolute", left:pct(now), top:0, bottom:0,
                width:2, background:"#ef4444", zIndex:3,
                boxShadow:"0 0 5px #ef444488",
              }}>
                <div style={{
                  position:"absolute", top:1, left:4,
                  background:"#ef4444", color:"#fff",
                  fontSize:8.5, fontWeight:700, padding:"1px 4px",
                  borderRadius:3, whiteSpace:"nowrap",
                }}>AUJOURD'HUI</div>
              </div>
            )}
            {milestones.map((m, i) => {
              const isHov = sel === `m${i}`;
              const size = m.type==="deadline" ? 16 : 12;
              return (
                <div key={i} style={{
                  position:"absolute", left:pct(m.day), top:"50%",
                  transform:"translate(-50%,-50%)", zIndex:2,
                }}
                  onMouseEnter={()=>setSel(`m${i}`)}
                  onMouseLeave={()=>setSel(null)}
                >
                  <div style={{
                    width:size, height:size,
                    background:MS_C[m.type],
                    transform:"rotate(45deg)",
                    margin:"0 auto",
                    boxShadow:`0 0 ${isHov?10:4}px ${MS_C[m.type]}88`,
                    transition:"box-shadow .2s",
                    cursor:"pointer",
                  }}/>
                  {isHov && (
                    <div style={{
                      position:"absolute", top: -(size/2 + 34), left:"50%",
                      transform:"translateX(-50%)",
                      background:"#ffffff", color:"#1e293b",
                      border:`1px solid ${MS_C[m.type]}88`,
                      fontSize:10.5, padding:"4px 10px", borderRadius:6,
                      whiteSpace:"nowrap",
                      boxShadow:"0 2px 14px rgba(0,0,0,.15)",
                      zIndex:10, fontWeight:500,
                    }}>
                      {m.label}
                      <div style={{
                        position:"absolute", bottom:-5, left:"50%",
                        transform:"translateX(-50%)",
                        borderLeft:"5px solid transparent",
                        borderRight:"5px solid transparent",
                        borderTop:`5px solid #ffffff`,
                      }}/>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr 1fr", gap:10, marginTop:16 }}>
        {["Jonathan","Ahmed","Jérémy","Antoine"].map(owner => {
          const c = C[owner.toLowerCase()];
          const ot = tasks.filter(t=>t.owner===owner);
          const roleDesc = owner === "Jonathan" ? "Chef Projet + Détection" : 
                          owner === "Ahmed" ? "Architecte Données (Python)" :
                          owner === "Jérémy" ? "Red Team + Visualisation" :
                          "Infrastructure + eBPF";
          return (
            <div key={owner} style={{
              background:"#ffffff", borderRadius:10,
              border:`1.5px solid ${c.dark}22`,
              padding:"11px 13px",
            }}>
              <div style={{
                fontSize:12.5, fontWeight:700, color:c.dark,
                borderBottom:`1px solid ${c.dark}15`,
                paddingBottom:4, marginBottom:3, letterSpacing:.5,
              }}>{owner}</div>
              <div style={{ fontSize:9, color:"#94a3b8", marginBottom:6, fontStyle:"italic" }}>
                {roleDesc}
              </div>
              {ot.slice(0, 5).map(t => (
                <div key={t.id} style={{ display:"flex", alignItems:"flex-start", gap:6, padding:"2.5px 0" }}>
                  <div style={{ width:7,height:7,borderRadius:1.5,background:PHASE_C[t.phase],marginTop:5,minWidth:7 }}/>
                  <div style={{ fontSize:10, color:"#475569" }}>
                    <span style={{ fontWeight:600 }}>{t.task}</span>
                    <span style={{ color:"#94a3b8", fontWeight:400 }}> — {fmtDate(t.start)} → {fmtDate(t.end)}</span>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>

      <p style={{ textAlign:"center", fontSize:10, color:"#94a3b8", marginTop:14 }}>
        Survolez les barres & jalons pour détails · Cliquez sur tâches pour éditer · Ligne rouge = aujourd'hui ({fmtDate(now || 0)})
      </p>
    </div>
  );
}