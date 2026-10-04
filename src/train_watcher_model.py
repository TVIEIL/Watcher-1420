import os
import pickle
import mysql.connector
import numpy as np
from sklearn.ensemble import IsolationForest

# --- Configuration de la base de données ---
DB_CONFIG = {
    'host': 'localhost',
    'database': 'radio_surveillance',
    'user': 'watcher',
    'password': 'mon_mot_de_passe'  # Ton mot de passe base de données
}

MODEL_PATH = 'watcher_model.pkl'  # Ajuste le chemin vers ton fichier .pkl si besoin

def load_data_from_db():
    print("[INFO] Connexion à MariaDB pour récupérer le dataset...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # On récupère les caractéristiques pertinentes pour l'apprentissage
    # Par exemple, max_power et avg_power (tu peux en rajouter si besoin)
    query = "SELECT max_power, avg_power FROM observations ORDER BY id ASC;"
    cursor.execute(query)
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not rows:
        print("[AVERTISSEMENT] Aucune donnée trouvée dans la table observations !")
        return None
        
    data = np.array(rows, dtype=np.float32)
    print(f"[INFO] {len(data)} enregistrements chargés depuis la base.")
    return data

def train_model(data):
    print("[INFO] Entraînement du modèle Isolation Forest...")
    
    # contamination='auto' ou une petite valeur (ex: 0.01) si tu penses qu'il y a très peu d'anomalies dans ton lot
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(data)
    
    print("[INFO] Entraînement terminé avec succès.")
    return model

def save_model(model):
    print(f"[INFO] Sauvegarde du modèle dans {MODEL_PATH}...")
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print("[INFO] Modèle sauvegardé et prêt pour le Watcher !")

if __name__ == '__main__':
    dataset = load_data_from_db()
    if dataset is not None and len(dataset) > 10:
        model = train_model(dataset)
        save_model(model)
    else:
        print("[ERREUR] Pas assez de données pour entraîner le modèle (minimum 10 requis).")
