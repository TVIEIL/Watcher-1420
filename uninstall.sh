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
# Script de désinstallation globale pour le projet Watcher-1420
# Ce script arrête le service systemd, supprime la BDD MariaDB,
# retire l'environnement Conda et supprime le binaire rtl_power_fftw.
# ==============================================================================

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== [1/4] Arrêt et suppression du service systemd utilisateur ===${NC}"
systemctl --user stop watcher1420.service 2>/dev/null || true
systemctl --user disable watcher1420.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/watcher1420.service"
systemctl --user daemon-reload
systemctl --user reset-failed 2>/dev/null || true
echo -e "${GREEN}[OK] Service systemd désactivé et retiré.${NC}"

echo -e "${GREEN}=== [2/4] Suppression de la base de données MariaDB et de l'utilisateur ===${NC}"
sudo mariadb -e "DROP DATABASE IF EXISTS radio_surveillance;" 2>/dev/null || true
sudo mariadb -e "DROP USER IF EXISTS 'watcher'@'localhost';" 2>/dev/null || true
echo -e "${GREEN}[OK] Base MariaDB 'radio_surveillance' et utilisateur 'watcher' supprimés.${NC}"

echo -e "${GREEN}=== [3/4] Suppression de l'environnement Conda 'watcher1420' ===${NC}"
CONDA_DIR="$HOME/miniconda3"
if [ -f "$CONDA_DIR/etc/profile.d/conda.sh" ]; then
    source "$CONDA_DIR/etc/profile.d/conda.sh"
    conda deactivate 2>/dev/null || true
    conda env remove -n watcher1420 -y 2>/dev/null || true
    echo -e "${GREEN}[OK] Environnement Conda 'watcher1420' supprimé.${NC}"
else
    echo -e "${RED}[INFO] Miniconda non trouvé, étape ignorée.${NC}"
fi

echo -e "${GREEN}=== [4/4] Suppression du binaire rtl_power_fftw ===${NC}"
if [ -f "/usr/local/bin/rtl_power_fftw" ]; then
    sudo rm -f /usr/local/bin/rtl_power_fftw
    echo -e "${GREEN}[OK] Binaire /usr/local/bin/rtl_power_fftw supprimé.${NC}"
else
    echo -e "${RED}[INFO] Binaire rtl_power_fftw non présent dans /usr/local/bin.${NC}"
fi

echo -e "${GREEN}Nettoyage complet terminé avec succès !${NC}"
