import subprocess
import os
import datetime as dt
import numpy as np
import getpass

Version = "0.4"

print("Watcher-1420 : rtl_power_fftw Setup background noise profile HI ")
print(f"Thierry Vieil F4HRB  - Version : {Version} - August, 2026 ")

# --- Configuration ---
START_FREQ =  1419500000      # 1.4195G en Hz
END_FREQ =    1421500000      # 1.4215G en Hz
BIN_COUNT = 16384
INTEGRATION_TIME = 45
GAIN = 40

# Commande sans l'option -m complexe, on capture la sortie standard directement
CMD_FFTW = f"rtl_power_fftw -f {START_FREQ}:{END_FREQ} -b {BIN_COUNT} -t {INTEGRATION_TIME} -g {GAIN}"

try:
    print(f"Lancement de l'acquisition du bruit de fond ({INTEGRATION_TIME}s)...")
    result = subprocess.run(CMD_FFTW, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Parsing direct des valeurs de puissance de la sortie standard
        baseline_data = [float(l.split()[1]) for l in result.stdout.splitlines() if not l.startswith('#') and l.strip()]
        
        if len(baseline_data) == BIN_COUNT:
            # Sauvegarde au format NumPy (.npy)
            np.save("baseline_hi.npy", np.array(baseline_data))
            print("Succès : Profil de bruit enregistré dans 'baseline_hi.npy'.")
            
            # Gestion des droits pour ton utilisateur
            current_user = getpass.getuser()
            subprocess.run(f"chown {current_user}:{current_user} baseline_hi.npy", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"chmod 644 baseline_hi.npy", shell=True)
        else:
            print(f"[ERREUR] Nombre de bins incorrects reçus : {len(baseline_data)} (attendu : {BIN_COUNT})")
    else:
        print(f"Erreur système RTL-SDR : {result.stderr}")

except FileNotFoundError:
    print("Erreur fatale : L'exécutable 'rtl_power_fftw' est introuvable.")
