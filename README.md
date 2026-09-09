# BookWorld

## Présentation

BookWorld est une entreprise fictive spécialisée dans la vente de livres en ligne.

L’objectif du projet est de collecter des données provenant de plusieurs sources, de les nettoyer et de les enrichir, puis de produire une agrégation des ventes par pays.

Les données finales sont stockées dans une base SQLite et exposées via une API REST.

## Sources utilisées

- `sales_raw.csv` : données brutes des ventes.
- `bookworld_reference.db` : base SQLite contenant les référentiels métier.
- `https://books.toscrape.com/` : catalogue de livres, avec scraping limité à la première page.
- API publique Frankfurter : récupération du taux de change GBP vers EUR.

## Installation

Les dépendances nécessaires sont indiquées dans le fichier `requirements.txt`.

Pour les installer :

pip install -r requirements.txt

## Exécuter le pipeline

Pour exécuter le pipeline :

python pipeline.py

Le pipeline :

- collecte les données provenant des différentes sources ;
- enrichit les ventes avec les informations nécessaires ;
- calcule les revenus en GBP et en EUR ;
- produit l'agrégation `sales_by_country` ;
- crée et alimente la base finale `business_data.db`.

## Lancer l'API

Pour lancer l'API :

python api.py

L'API est ensuite accessible à l'adresse :

http://127.0.0.1:5000

## Authentification

L'API utilise une authentification simple par Bearer token.

Le token est stocké dans un fichier `.env` à la racine du projet.

Le fichier `.env` doit contenir :

BOOKWORLD_API_TOKEN=your_token_here

Le fichier `.env` ne doit pas être publié sur GitHub.

Un fichier `.env.example` est fourni comme modèle :

BOOKWORLD_API_TOKEN=your_token_here

Pour accéder aux données métier, le token doit être envoyé dans l'en-tête HTTP :

Authorization: Bearer <token>

## Endpoints

### GET /health

Cet endpoint permet de vérifier que l'API fonctionne.

Exemple :

http://127.0.0.1:5000/health

Réponse attendue :

{
  "status": "ok"
}

Cet endpoint est accessible sans token.

### GET /sales-by-country

Cet endpoint retourne les ventes agrégées par pays.

L'accès à cet endpoint nécessite un token valide.

Exemple avec un Bearer token :

Authorization: Bearer <token>

L'endpoint retourne les informations suivantes :

- `country_code`
- `country_name`
- `total_orders`
- `total_quantity`
- `total_revenue_gbp`
- `total_revenue_eur`

## Structure des fichiers

- `pipeline.py` : extraction, nettoyage, enrichissement, agrégation et alimentation de la base finale.
- `api.py` : API REST développée avec Flask.
- `sales_raw.csv` : données brutes des ventes.
- `bookworld_reference.db` : base SQLite contenant les référentiels métier.
- `schema_final.sql` : structure de la base finale.
- `business_data.db` : base SQLite finale contenant les données agrégées.
- `queries.sql` : requêtes SQL utilisées pour l'extraction depuis la base de référence.
- `requirements.txt` : dépendances Python du projet.
- `.env` : configuration locale du token d'authentification.
- `.env.example` : modèle du fichier `.env`.
- `.gitignore` : fichiers qui ne doivent pas être versionnés.

## Base finale

La base finale contient la table `sales_by_country`.

Elle contient les données agrégées par pays nécessaires à l'utilisation de l'API.

Les noms et prénoms présents dans les données brutes ne sont pas conservés dans la base finale car ils ne sont pas nécessaires à l'objectif du projet.

## Publication sur GitHub

Le projet peut être versionné dans un dépôt GitHub.

Le fichier `.env` doit rester local et ne doit pas être publié.

Le fichier `.env.example` peut être publié afin d'indiquer la configuration nécessaire à l'utilisation du projet.