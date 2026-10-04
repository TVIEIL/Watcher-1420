#!/bin/bash

# Script d'installation globale pour le projet Watcher-1420
# Ce script installe Miniconda, configure l'environnement Conda, installe MariaDB,
# déploie le service Avahi mDNS, et configure un service systemd utilisateur pour le monitoring.

set -e

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[1/6] Installation de Miniconda3 (Architecture x86_64 / Intel)...${NC}"
CONDA_DIR="$HOME/miniconda3"
if [ ! -d "$CONDA_DIR" ]; then
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -u -p "$CONDA_DIR"
    rm miniconda.sh
    "$CONDA_DIR/bin/conda" init bash
    echo "Miniconda installé avec succès dans $CONDA_DIR."
else
    echo "Miniconda est déjà présent dans $CONDA_DIR."
fi

# Chargement de l'environnement conda pour la suite du script
source "$CONDA_DIR/etc/profile.d/conda.sh"

echo -e "${GREEN}[2/6] Création de l'environnement Conda 'watcher1420'...${NC}"
if conda env list | grep -q "watcher1420"; then
    echo "L'environnement 'watcher1420' existe déjà."
else
    conda create -y -n watcher1420 python=3.10
fi

echo -e "${GREEN}[3/6] Installation des dépendances depuis requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    conda activate watcher1420
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${RED}[ERREUR] Le fichier requirements.txt est introuvable à la racine.${NC}"
    exit 1
fi

echo -e "${GREEN}[4/6] Exécution du script d'installation de MariaDB...${NC}"
if [ -f "src/setup_mariadb.sh" ]; then
    chmod +x src/setup_mariadb.sh
    sudo ./src/setup_mariadb.sh
else
    echo -e "${RED}[ERREUR] Le script src/setup_mariadb.sh est introuvable.${NC}"
    exit 1
fi

echo -e "${GREEN}[5/6] Déploiement du service mDNS Avahi (deploy_watcher_service.sh)...${NC}"
if [ -f "src/deploy_watcher_service.sh" ]; then
    chmod +x src/deploy_watcher_service.sh
    sudo ./src/deploy_watcher_service.sh
else
    echo -e "${RED}[ERREUR] Le script src/deploy_watcher_service.sh est introuvable.${NC}"
    exit 1
fi

echo -e "${GREEN}[6/6] Création et activation du service systemd utilisateur pour Watcher-1420...${NC}"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$CONDA_DIR/envs/watcher1420/bin/python"
SCRIPT_PATH="$PROJECT_DIR/src/monitor_ia_watcher_ZMQ_STANDARD_V6_9_1.py"

SERVICE_FILE="$SERVICE_DIR/watcher1420.service"

cat << EOF > "$SERVICE_FILE"
[Unit]
Description=Watcher-1420 Radioastronomy Monitoring Service
After=network.target mysql.service

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR/src
ExecStart=$PYTHON_PATH $SCRIPT_PATH
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

# Rechargement et activation du service systemd pour l'utilisateur courant
systemctl --user daemon-reload
systemctl --user enable watcher1420.service

echo -e "${GREEN}Installation globale terminée avec succès !${NC}"
echo -e "Pour démarrer le service de monitoring : ${GREEN}systemctl --user start watcher1420${NC}"
echo -e "Pour consulter les logs : ${GREEN}journalctl --user -u watcher1420 -f${NC}"
