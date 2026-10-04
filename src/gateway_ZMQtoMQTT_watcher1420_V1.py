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

import zmq
import json
import paho.mqtt.client as mqtt
import time
import os
import subprocess

# --- Configuration ---
# L'IP du Watcher1420 (Le conteneur ZMQ devra pouvoir la joindre sur le port 5555)
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT avec succès.")
    else:
        print(f"Échec de connexion MQTT, code : {rc}")

# Initialisation MQTT

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Initialisation ZMQ (PULL et CONNECT)
context = zmq.Context()
socket = context.socket(zmq.PULL) 
socket.set(zmq.RCVHWM, 10)

# CHANGEMENT ICI : on lie le port pour écouter les connexions entrantes
# On écoute sur toutes les interfaces (0.0.0.0) sur le port 5555
socket.bind("tcp://0.0.0.0:5555")

print(f"--- Passerelle ZMQ -> MQTT en ligne (Écoute sur port 5555) ---")
  
    
try:
    while True:
        try:
            # Réception du JSON
            message = socket.recv_json()
            print(f"Message reçu : {message}")
                    
            # Exemple de message
            #{
            # "timestamp": "2026-07-18T20:34:23.123456",
            # "status": "ANOMALIE",
            # "max_power": 12.5,
            # "avg_power": 8.2
            #}
            
            topic = None
            if message.get("status") == "ANOMALIE":
                topic = "natacha/watcher/anomalies"
            
            if topic:
                mqtt_client.publish(topic, json.dumps(message))
                print(f"Message publié sur {topic}")
                
        except zmq.ZMQError as e:
            print(f"Erreur ZMQ : {e}. Tentative de maintien de la connexion...")
            time.sleep(5)
        except Exception as e:
            print(f"Erreur inattendue dans la boucle : {e}")
            time.sleep(5) # Pause pour éviter de saturer le processeur en cas de crash en boucle

except KeyboardInterrupt:
    print("\nArrêt de la passerelle par l'utilisateur.")
finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    socket.close()
    context.term()
