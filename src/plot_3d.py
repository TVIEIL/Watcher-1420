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

import mysql.connector
import pandas as pd
import plotly.express as px

# 1. Connexion à ta base MariaDB locale
conn = mysql.connector.connect(
    host="localhost",
    user="watcher",  # Remplace par ton user
    password="mon_mot_de_passe",  # Remplace par ton mot de passe
    database="radio_surveillance",
)

# 2. Récupération des données dans un DataFrame Pandas
query = "SELECT ra, `dec`, max_power, status FROM observations"
df = pd.read_sql(query, conn)
conn.close()

# 3. Création du graphique 3D interactif avec Plotly
fig = px.scatter_3d(
    df,
    x="ra",
    y="dec",
    z="max_power",
    color="status",  # Vert pour calme, rouge/autre pour anomalie
    title="Watcher-1420 : Nuage de points 3D (RA vs DEC vs Puissance)",
    labels={
        "ra": "Ascension Droite (RA)",
        "dec": "Déclinaison (DEC)",
        "max_power": "Puissance Max (dBm)",
    },
    color_discrete_map={
        "CALME": "green",
        "ANOMALIE": "red",
    },  # Adapte selon tes libellés de status
    opacity=0.7,
)

# 4. Affichage du graphique dans le navigateur web par défaut
fig.show()
