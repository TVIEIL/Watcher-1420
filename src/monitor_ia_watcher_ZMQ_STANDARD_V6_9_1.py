import numpy as np
import subprocess
import time
import joblib
import pandas as pd
import mysql.connector
import os
import zmq
import json
from skyfield.api import load, wgs84
from datetime import datetime, timedelta
import sys

version = "6.9.1"

# Variable pour retenir le dernier timestamp généré (en dehors de la boucle)
last_timestamp = None

# Initialisation du compteur de resets en dehors de la boucle
consecutive_resets = 0
MAX_CONSECUTIVE_RESETS = 3

# Définis le timescale 
ts = load.timescale()

MQTT_KIWIX_HOST = "MQTT-KIWIX.local"

# --- Configuration ---
START_FREQ = 1420355750      # Hz
END_FREQ = 1420455750        # Hz
BIN_COUNT = 16384
INTEGRATION_TIME = 45        # Modifié à 45 secondes
GAIN = 40

# Calculs automatiques
CENTER_FREQ_MHZ = ((START_FREQ + END_FREQ) / 2) / 1_000_000
BANDWIDTH_HZ = END_FREQ - START_FREQ
RESOLUTION_HZ = BANDWIDTH_HZ / BIN_COUNT

FIXED_AZ, FIXED_ALT = 240.0, 60.0

# Commande FFTW
CMD_FFTW = f"rtl_power_fftw -f {START_FREQ}:{END_FREQ} -b {BIN_COUNT} -t {INTEGRATION_TIME} -g {GAIN}"

# Définit les chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_FILE = os.path.join(BASE_DIR, "wav", "anomalie_detectee.wav")
DATA_DIR = "anomalies_data"
LOG_BUFFER = []
BATCH_SIZE = 20

DB_CONFIG = {
    'host': "localhost",
    'user': "watcher",
    'password': "mon_mot_de_passe",
    'database': "radio_surveillance"
}

def reset_dongle():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Réinitialisation matérielle du port USB (3-2)...")
    reset_cmd = (
        'echo "3-2" | sudo tee /sys/bus/usb/drivers/usb/unbind && '
        'sleep 3 && '
        'echo "3-2" | sudo tee /sys/bus/usb/drivers/usb/bind'
    )
    subprocess.run(reset_cmd, shell=True)
    print("Réinitialisation terminée. Attente de stabilisation...")
    time.sleep(5)

def is_machine_up(host):
    command = ["ping", "-c", "3", host]
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0
    
def connect_to_communication_server():
    global context
    for attempt in range(1, 4):
        print(f"Tentative {attempt}/3 de connexion à {MQTT_KIWIX_HOST}...")
        if is_machine_up(MQTT_KIWIX_HOST):
            try:
                socket = context.socket(zmq.PUSH)
                socket.set(zmq.SNDHWM, 10)
                socket.connect(f"tcp://{MQTT_KIWIX_HOST}:5555")
                print("Connexion au serveur de communication établie.")
                return socket
            except Exception as e:
                print(f"Erreur lors de la connexion (essai {attempt}) : {e}")
        else:
            print(f"Machine {MQTT_KIWIX_HOST} injoignable.")
        if attempt < 3:
            time.sleep(10)
    print("Échec après 3 tentatives. Le Watcher continue sans connexion au serveur de com.")
    return None

def get_sidereal_time():
    t = ts.now()
    return t.gmst

def get_celestial_coords():
    t = load.timescale().now()
    altaz = montsoult.at(t).from_altaz(alt_degrees=FIXED_ALT, az_degrees=FIXED_AZ)
    ra, dec, _ = altaz.radec()
    return ra.hours, dec.degrees

def log_to_db(freq_hz, max_p, avg_p, status, ra, dec, lst_time, center_freq, res_hz, gain, temp):
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """INSERT INTO observations 
                   (frequency_hz, max_power, avg_power, status, ra, `dec`, lst_time, center_freq_mhz, resolution_hz, gain, temp_celsius) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (int(freq_hz), float(max_p), float(avg_p), status, float(ra), float(dec), 
                               float(lst_time), float(center_freq), float(res_hz), float(gain), float(temp)))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Erreur DB Unitaire : {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()

# --- Initialisation ---
context = zmq.Context()
socket = connect_to_communication_server()

montsoult = wgs84.latlon(49.07, 2.33)   # Montsoult - Val d'Oise - France
model = joblib.load('watcher_model.pkl')

print(f"--- Watcher-1420 (V{version}) : Système en ligne (Baseline 45s). ---")

try:
    while True:
        try:
            print("Stabilisation du système et du tuner SDR", end="", flush=True)
            for i in range(5, 0, -1):
                print(f". {i}s", end="", flush=True)
                time.sleep(1)
            print(" -> Prêt !\n")

            result = subprocess.run(CMD_FFTW, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                # print(result.stdout, flush=True) #old on affiche tout imbitable
                lines = result.stdout.splitlines()
                # On affiche l'en-tête ou les 10 premières lignes
                for line in lines[:10]:
                    print(line, flush=True)
                if len(lines) > 10:
                    print(f"    [... {len(lines) - 10} lignes supplémentaires masquées ...]", flush=True)
                
                
          
            if result.returncode != 0:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Erreur acquisition : {result.returncode}\r\n", end="", flush=True)
                stderr_output = str(result.stderr) if result.stderr else ""
                
                if "usb_claim_interface" in stderr_output or "error -5" in stderr_output or result.returncode != 0:
                    consecutive_resets += 1
                    print(f"[ALERTE] Incident matériel détecté (Tentative de reset {consecutive_resets}/{MAX_CONSECUTIVE_RESETS})")
                    if consecutive_resets > MAX_CONSECUTIVE_RESETS:
                        print("[CRITIQUE] Trop d'échecs consécutifs. Pause de 15 minutes...")
                        time.sleep(900)
                        consecutive_resets = 0
                    else:
                        reset_dongle()
                        time.sleep(10)
                continue  
            else:
                consecutive_resets = 0

            # Parsing des données
            data = [float(l.split()[1]) for l in result.stdout.splitlines() if not l.startswith('#') and l.strip()]

            if data:
                max_p, avg_p = np.max(data), np.mean(data)
                pred = model.predict(pd.DataFrame([[max_p, avg_p]], columns=['max_power', 'avg_power']))[0]
                
                print(f"[DEBUG] max_p={max_p:.2f}, avg_p={avg_p:.2f} -> Prediction IA: {pred} | Buffer size: {len(LOG_BUFFER)}")
                
                ra, dec = get_celestial_coords()
                lst_time = get_sidereal_time()
                temp_celsius = 25.0 
                
                if pred == -1:
                    # Traitement ANOMALIE
                    log_to_db(int(CENTER_FREQ_MHZ * 1_000_000), max_p, avg_p, "ANOMALIE", ra, dec, lst_time, CENTER_FREQ_MHZ * 1_000_000, RESOLUTION_HZ, GAIN, temp_celsius)
                    
                    if socket is not None:
                        alert_payload = {"timestamp": datetime.now().isoformat(), "status": "ANOMALIE", "max_power": float(max_p), "avg_power": float(avg_p)}
                        socket.send_json(alert_payload)
                    
                    ts_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    os.makedirs(DATA_DIR, exist_ok=True)
                    filename = os.path.join(DATA_DIR, f'anomalie_{ts_str}.txt')
                    temp_filename = filename + ".tmp"

                    with open(temp_filename, 'w') as f:
                        f.write(f"# Timestamp: {datetime.now()}\n")
                        f.write(f"# Start Freq: {START_FREQ}\n")
                        f.write(f"# End Freq: {END_FREQ}\n")
                        f.write(f"# Bin Count: {len(data)}\n")
                        f.write(f"# Max Power: {max_p}, Avg Power: {avg_p}\n")
                        for val in data:
                            f.write(f"{val}\n")
                    
                    os.rename(temp_filename, filename)
                    subprocess.Popen(["aplay", "-q", SOUND_FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"\n[ALERTE] Anomalie détectée et enregistrée dans {filename}")
                
                else:
                    # Enregistrement CALME dans le buffer
                    current_real_time = datetime.now()
                    if last_timestamp is None or last_timestamp < current_real_time:
                        base_time = current_real_time
                    else:
                        base_time = last_timestamp + timedelta(seconds=8)
                        
                    point_timestamp = base_time
                    last_timestamp = point_timestamp  
                    
                    LOG_BUFFER.append((
                        point_timestamp,
                        int(CENTER_FREQ_MHZ * 1_000_000), 
                        float(max_p), 
                        float(avg_p), 
                        "CALME", 
                        float(ra), 
                        float(dec), 
                        float(lst_time), 
                        float(CENTER_FREQ_MHZ * 1_000_000), 
                        float(RESOLUTION_HZ), 
                        float(GAIN), 
                        float(temp_celsius)
                    ))
                    
                    # --- NOUVEAU : Affichage clair du compteur en direct ---
                    print(f"[INFO] Mesure CALME ajoutée. Buffer : {len(LOG_BUFFER)}/{BATCH_SIZE}")
                
                # Gestion Batch DB (écriture par lots de BATCH_SIZE)
                if len(LOG_BUFFER) >= BATCH_SIZE:
                    print(f"[INFO] Seuil de {BATCH_SIZE} atteint. Tentative d'écriture dans MariaDB...")
                    try:
                        conn = mysql.connector.connect(**DB_CONFIG)
                        cursor = conn.cursor()
                        cursor.executemany(
                            "INSERT INTO observations (timestamp, frequency_hz, max_power, avg_power, status, ra, `dec`, lst_time, center_freq_mhz, resolution_hz, gain, temp_celsius) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                            LOG_BUFFER
                        )
                        conn.commit()
                        cursor.close()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Succès ! Batch de {BATCH_SIZE} observations inséré dans MariaDB.")
                        LOG_BUFFER = []
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Batch de {BATCH_SIZE} observations inséré dans MySQL.")
                    except Exception as e:
                        print(f"\nErreur DB Batch : {e}")
                    finally:
                        if conn and conn.is_connected(): 
                            conn.close()
            
            time.sleep(0.5)

        except subprocess.TimeoutExpired:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Timeout détecté.\n", flush=True)
            time.sleep(5)

        except Exception as e:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Erreur critique : {e}")
            time.sleep(5)
            continue

except KeyboardInterrupt:
    print("\nArrêt manuel du Watcher-1420.")
