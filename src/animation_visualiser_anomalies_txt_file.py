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

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import glob
import numpy as np
import os

# 1. Lister tous tes fichiers d'anomalies
files = sorted(glob.glob("anomalies_data/anomalie_*.txt"))

fig, ax = plt.subplots(figsize=(10, 6))

def update(frame):
    ax.clear()
    filename = files[frame]
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    start_freq = 0
    end_freq = 0
    bin_count = 0
    
    # Lecture dynamique
    for line in lines:
        if "# Start Freq:" in line:
            start_freq = float(line.split(': ')[1])
        elif "# End Freq:" in line:
            end_freq = float(line.split(': ')[1])
        elif "# Bin Count:" in line:
            bin_count = int(line.split(': ')[1])
            
    # Vérification de sécurité pour éviter le plantage
    if start_freq == 0 or bin_count == 0:
        print(f"Erreur de lecture sur le fichier : {filename}")
        print(f"DEBUG -> Start: {start_freq}, Bin: {bin_count}")
        return # Arrête cette image pour éviter le plantage
    
    data = [float(l.strip()) for l in lines if not l.startswith('#')]
    freqs = np.linspace(start_freq, end_freq, bin_count)
    
    # Tracé
    ax.plot(freqs / 1e6, data, color='blue', linewidth=0.5)
    ax.set_ylim(-68, -60)
    ax.set_title(f"Anomalie : {os.path.basename(filename)}")


ani = animation.FuncAnimation(fig, update, frames=len(files), interval=500)
plt.show()
