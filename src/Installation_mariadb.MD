# Installation de mariadb  setup_mariadb.sh 

## 1.Rendre le script exécutable :
bash
``` 
chmod +x setup_mariadb.sh
```
donnez-lui les droits d'exécution :
Bash
```
chmod +x setup_mariadb.sh
```
## 2.Lancer le script d'installation :
Bash
```
sudo ./setup_mariadb.sh
```


## 3.Vérifier la table en base de données :
 .Connectez-vous à MariaDB pour valider la structure de la table :
 Bash
 ```
 sudo mysql -u watcher -pmot_de_passe radio_surveillance -e "DESCRIBE observations;"
 ```
La sortie de la commande doit afficher l'ensemble des 13 colonnes requises (id, timestamp, frequency_hz, max_power, etc.).
