
# **Linkedin Webscrapping**

## **Description**

Ce projet a pour objectif de fournir un outil permettant d'identifier les tendances sur le thème bien precis sur la plateforme linkedin

L'outil extrait automatiquement des posts LinkedIn liés à des mots-clés spécifiques, les traite et les stocke dans une base de données PostgreSQL. Un tableau de bord a été créé dans Google Data Studio pour visualiser les données  et un worflow N8n peut travailler sur ses données.

## **Fonctionnalités**

1. **Extraction de données LinkedIn** :
   - Recherche automatique de posts liés à des mots-clés pertinents (ex. "cybersécurité + Afrique") via Selenium et BeautifulSoup.
   - Extraction d'informations des posts comme le texte, la date, l'auteur, etc.

2. **Stockage des données** :
   - Stockage des posts extraits dans une base de données PostgreSQL pour un usage futur.

3. **Visualisation des données** :
   - Création de tableaux de bord interactifs dans Google Data Studio pour l'équipe CAF.

4. **Étude comparative de techniques de modélisation de données** :
   - Analyse des schémas de modélisation des données (ex. Star Schema, Snowflake, Data Vault 2.0) pour une optimisation du stockage et de l'accès aux données.

## **Prérequis**

Avant de commencer, assurez-vous d'avoir les éléments suivants :

- Un compte Linkedin
- Python 3.x
- Jupyter Notebook ou tout autre éditeur de editeur de code
- Google Data Studio (pour visualiser les données)

## **Installation**

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/projet-caf.git
```

### 2. Créer un environnement virtuel et l'activer

```bash
python -m venv venv
source venv/bin/activate   # Sur macOS/Linux
venv\Scripts\activate      # Sur Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet et y ajouter les informations de configuration, comme l'exemple suivant :

```bash
# Fichier .env

DB_HOST=localhost
DB_NAME=your_db_name
DB_USER=your_username
DB_PASSWORD=your_password
USERNAME=your_linkedin_usernameoremail
PASSWORD=your_linkedin_password
MOTS_CLES=cybersécurité,IA,Afrique
```

### 5. Configuration de la base de données

Créez une base de données PostgreSQL locale ou utilisez un service comme [Aiven](https://aiven.io/) pour stocker les données. Vous pouvez adapter les informations de connexion dans le fichier `.env`.

### 6. Lancer le script d'extraction

Vous pouvez exécuter le script dans un notebook Jupyter ou dans un script Python classique pour commencer l'extraction des posts LinkedIn en fonction des mots-clés.

Via le notebook
```bash
jupyter notebook
```

Ou directement via le fichier python :

```bash
python getdata.py
```

## **Utilisation**

- **Extraction des données** : Le script utilise Selenium et BeautifulSoup pour récupérer des posts LinkedIn basés sur des mots-clés. Les données sont ensuite stockées dans PostgreSQL.
- **Accès aux données** : Les données peuvent être visualisées via le tableau de bord Google Data Studio connecté à la base de données.

## **Dépendances**

Voici les principales dépendances utilisées dans ce projet :

- `selenium`
- `webdriver-manager`
- `beautifulsoup4`
- `pandas`
- `psycopg2-binary`
- `python-dateutil`
- `python-dotenv`

Voir le fichier [requirements.txt](requirements.txt) pour une liste complète.


## **Auteur**

Josué Kouassi  

**Contact** : kouassijosue1268@gmail.com
**LinkedIn** : www.linkedin.com/in/josué-kouassi-538225292
