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
