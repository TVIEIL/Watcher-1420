import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# --- Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'watcher',
    'password': 'mon_mot_de_passe',
    'database': 'radio_surveillance'
}

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

def update(frame):
    ax.clear()
    # Configuration de la vue isométrique
    ax.view_init(elev=30, azim=45)
    
    # Récupération des 50 dernières données
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id, max_power, status FROM observations ORDER BY id DESC LIMIT 50")
    data = cursor.fetchall()[::-1]
    conn.close()

    if not data:
        return

    ids = [i for i in range(len(data))]
    raw_z = [row[1] for row in data]
    
    # Application de l'amplification sur l'axe Z
    base_val = -49.5
    z = [(val - base_val) * 1000 for val in raw_z]
    
    # Pour tracer une ligne 3D propre, on peut segmenter par couleur ou tracer une ligne globale
    # Ici on trace la ligne principale en vert/rouge selon les points
    for i in range(len(ids) - 1):
        color = 'red' if (data[i][2] == 'ANOMALIE' or data[i+1][2] == 'ANOMALIE') else '#00ff00'
        ax.plot(ids[i:i+2], [0, 0], z[i:i+2], color=color, linewidth=2.5)

    # Ajout d'une projection au sol pour donner du relief
    ax.scatter(ids, [0]*len(ids), z, c=['red' if row[2] == 'ANOMALIE' else '#00ff00' for row in data], s=20)
    
    # Bornes et esthétique
    ax.set_zlim(min(z) - 50, max(z) + 50)
    ax.set_ylim(-0.5, 0.5)
    
    ax.set_title("Watcher-1420 : Trajectoire Spectrale 3D")
    ax.set_xlabel("Index")
    ax.set_ylabel("Flux")
    ax.set_zlabel("Puissance Amplifiée")

# Rafraîchissement toutes les 60000ms (60 secondes)
ani = FuncAnimation(fig, update, interval=60000)

plt.show()
