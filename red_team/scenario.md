# 🏴‍☠️ Scénarios d'Attaques (Red Team)

Ce dossier rassemble l'ensemble des scripts nécessaires pour prouver l'efficacité de la détection de **Sentinel-Graph** face à des attaques dites *Zero-Day* ou comportements anormaux.

Notre IDS étant comportemental (non basé sur des signatures statiques), le but ici est d'utiliser un pod réputé sain qui, soudainement, change de comportement.

## 🛠 Préparation : Le Pod Victime (Patient Zéro)

1. Ouvrez un terminal.
2. Créez un conteneur d'expérimentation légitime qui tourne en tâche de fond :
   ```bash
   kubectl run victime-pod -it --rm --image=alpine -- sh
   ```
3. Laissez le terminal tourner. La baseline considérera que ce pod (qui ne fait rien) est inoffensif.

---

## 💣 Exécution des Scénarios d'Attaque

### Scénario 1 : Le Reverse Shell (Intrusion C2)
L'attaquant exploite une vulnérabilité (simulée ici) pour forcer le pod victime à appeler un serveur Command & Control externe via `netcat`.

1. Dans un **nouveau terminal**, injectez et exécutez le script dans le pod victime :
   ```bash
   kubectl cp red_team/attacks/reverse_shell.sh victime-pod:/tmp/reverse_shell.sh
   kubectl exec -it victime-pod -- sh /tmp/reverse_shell.sh
   ```
**Observation Dashboard :**
Vous observerez l'enfant `sh` spawner l'exécutable masqué `nc` (netcat) couplé à une tentative réseau vers l'extérieur (IP C2). Les alertes `UNKNOWN_PROCESS` vont pleuvoir.

---

### Scénario 2 : L'Exfiltration de Données (Vol de Secrets)
L'attaquant est déjà dans l'infrastructure et cherche à lire de la donnée interne sensible (`/etc/passwd`) avant de l'envoyer massivement à l'extérieur via une requête `POST`.

1. Injectez l'attaque d'exfiltration :
   ```bash
   kubectl cp red_team/attacks/exfiltration.sh victime-pod:/tmp/exfiltration.sh
   kubectl exec -it victime-pod -- sh /tmp/exfiltration.sh
   ```
**Observation Dashboard :**
La lecture inhabituelle via l'utilitaire `cat` de la volumétrie système sera détectée, ainsi que la connexion inattendue au serveur web distant via l'utilitaire `curl`.

---

### Analyse et Conclusion
Ces scénarios montrent comment **Tetragon** au niveau eBPF logge les appels systèmes, et comment notre algorithme de **Baseline** NetworkX calcule immédiatement l'écart sans jamais avoir connu ces scripts `.sh` au préalable (l'essence de la détection Zero-Day).
