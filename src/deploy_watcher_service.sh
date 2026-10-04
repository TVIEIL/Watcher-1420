#!/bin/bash

# 1. Vérification root
if [[ $EUID -ne 0 ]]; then
   echo "Erreur : Ce script doit être lancé avec sudo." 
   exit 1
fi

echo "--- Déploiement dynamique du service Watcher-1420 ---"

# 2. Installation
apt update && apt install -y avahi-daemon

# 3. Récupération des infos machine
MACHINE_NAME=$(hostname)

# 4. Création du fichier de service enrichi
cat <<EOF > /etc/avahi/services/watcher.service
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Watcher-1420 (%h)</name>
  <service>
    <type>_zmq._tcp</type>
    <port>5555</port>
    <txt-record>role=radio_astronomy</txt-record>
    <txt-record>target=hydrogen_line_1420MHz</txt-record>
    <txt-record>location=montsoult_lab</txt-record>
    <txt-record>hostname=$MACHINE_NAME</txt-record>
    <txt-record>version=2.0</txt-record>
  </service>
</service-group>
EOF

# 5. Activation
systemctl enable avahi-daemon
systemctl restart avahi-daemon

echo "--- Déploiement terminé ! ---"
echo "Service publié sous : Watcher-1420 ($MACHINE_NAME)"
echo "Natacha peut désormais lire les métadonnées sur le port 5555."
