#!/bin/bash

# Script d'installation et de configuration de MariaDB pour le projet Watcher-1420
# Utilisateur : watcher | Mot de passe : 031274 | Base : radio_surveillance

set -e

echo "[1/4] Installation de MariaDB Server..."
sudo apt update
sudo apt install -y mariadb-server

echo "[2/4] Démarrage et activation du service MariaDB..."
sudo systemctl start mariadb
sudo systemctl enable mariadb

echo "[3/4] Création de la base de données et de l'utilisateur..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS radio_surveillance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'watcher'@'localhost' IDENTIFIED BY 'mon_mot_de_passe';"
sudo mysql -e "GRANT ALL PRIVILEGES ON radio_surveillance.* TO 'watcher'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "[4/4] Création de la table observations..."
sudo mysql radio_surveillance <<EOF
CREATE TABLE IF NOT EXISTS observations (
    id bigint(20) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    timestamp datetime(6) DEFAULT current_timestamp(6),
    frequency_hz bigint(20) NOT NULL,
    max_power float NOT NULL,
    avg_power float DEFAULT NULL,
    status varchar(20) DEFAULT NULL,
    ra float DEFAULT NULL,
    \`dec\` float DEFAULT NULL,
    lst_time float DEFAULT NULL,
    center_freq_mhz float DEFAULT NULL,
    resolution_hz float DEFAULT NULL,
    gain float DEFAULT NULL,
    temp_celsius float DEFAULT NULL
);
EOF

echo "Installation et configuration de MariaDB terminées avec succès !"
