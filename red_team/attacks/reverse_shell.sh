#!/bin/sh
# Simulation simplifiée d'un Reverse Shell pour déclencher une déviation (UNEXPECTED_SPAWN + UNEXPECTED_CONNECTION)
echo "🚨 [RED TEAM] Exécution de la charge utile : Reverse Shell"

# 1. Utilisation inhabituelle d'outils système (suspicious execve)
echo "   [+] Installation d'outils suspects (netcat)..."
apk add --no-cache netcat-openbsd > /dev/null 2>&1

# 2. Exécution d'un sous-shell (fork/execve suspect)
echo "   [+] Tentative de connexion sortante (C2)..."
sh -c 'nc -zvw1 8.8.8.8 443' 2>/dev/null

echo "✅ Attaque terminée. Regardez le tableau de bord Sentinel-Graph !"
