#!/bin/bash

# Copyright 2026 Thierry VIEIL / Natacha Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ==============================================================================
# Script d'installation globale pour le projet Watcher-1420
# Ce script installe les dépendances système (FFTW, RTL-SDR, TCLAP), compile
# rtl_power_fftw, configure Miniconda et l'environnement Conda, installe
# MariaDB, déploie Avahi mDNS et configure le service systemd utilisateur.
# ==============================================================================

set -e

# Capture du répertoire racine du projet dès le départ
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== [1/3] Installation des dépendances système ===${NC}"
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    pkg-config \
    libfftw3-dev \
    librtlsdr-dev \
    libtclap-dev \
    git \
    wget

echo -e "${GREEN}=== [2/3] Compilation et installation de rtl_power_fftw ===${NC}"
BUILD_DIR=$(mktemp -d)
cd "$BUILD_DIR"

# Clonage du dépôt AD-Vega
git clone https://github.com/AD-Vega/rtl-power-fftw.git
cd rtl-power-fftw

mkdir -p build && cd build
# Ingestion du flag CMAKE_POLICY_VERSION_MINIMUM pour la compatibilité CMake >= 3.5 / 4.x
cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5
make -j$(nproc)
sudo make install
sudo ldconfig

# Nettoyage des fichiers temporaires de compilation
rm -rf "$BUILD_DIR"

# Retour impératif dans le dossier du projet
cd "$PROJECT_DIR"

echo -e "${GREEN}=== [3/3] Vérification de l'installation ===${NC}"
if command -v rtl_power_fftw >/dev/null 2>&1; then
    echo -e "${GREEN}[OK] rtl_power_fftw a été installé avec succès dans $(which rtl_power_fftw)${NC}"
else
    echo -e "${RED}[ERREUR] L'installation de rtl_power_fftw a échoué.${NC}"
    exit 1
fi

echo -e "${GREEN}[1/7] Neutralisation du pilote DVB conflictuel pour la RTL-SDR...${NC}"
echo "blacklist dvb_usb_rtl28xxu" | sudo tee /etc/modprobe.d/blacklist-rtl.list > /dev/null
sudo update-initramfs -u > /dev/null 2>&1 || true

echo -e "${GREEN}[2/7] Installation de Miniconda3 (Architecture x86_64 / Intel)...${NC}"
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

echo -e "${GREEN}[3/7] Création de l'environnement Conda 'watcher1420'...${NC}"
if conda env list | grep -q "watcher1420"; then
    echo "L'environnement 'watcher1420' existe déjà."
else
    conda create -y -n watcher1420 python=3.10
fi

echo -e "${GREEN}[4/7] Installation des dépendances depuis requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    conda activate watcher1420
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${RED}[ERREUR] Le fichier requirements.txt est introuvable à la racine ($PROJECT_DIR).${NC}"
    exit 1
fi

echo -e "${GREEN}[5/7] Exécution du script d'installation de MariaDB...${NC}"
if [ -f "src/setup_mariadb.sh" ]; then
    chmod +x src/setup_mariadb.sh
    sudo ./src/setup_mariadb.sh
else
    echo -e "${RED}[ERREUR] Le script src/setup_mariadb.sh est introuvable.${NC}"
    exit 1
fi

echo -e "${GREEN}[6/7] Déploiement du service mDNS Avahi (deploy_watcher_service.sh)...${NC}"
if [ -f "src/deploy_watcher_service.sh" ]; then
    chmod +x src/deploy_watcher_service.sh
    sudo ./src/deploy_watcher_service.sh
else
    echo -e "${RED}[ERREUR] Le script src/deploy_watcher_service.sh est introuvable.${NC}"
    exit 1
fi

echo -e "${GREEN}[7/7] Création et activation du service systemd utilisateur pour Watcher-1420...${NC}"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

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
