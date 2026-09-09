# BookWorld — Pipeline de données multi-sources

Projet pédagogique de Data Analyse / Data Engineering.

L’objectif est de construire un pipeline capable de :

- collecter des données depuis plusieurs sources ;
- nettoyer et enrichir ces données ;
- produire une agrégation métier exploitable ;
- créer une base SQLite finale ;
- exposer cette agrégation via une API REST ;
- documenter le projet pour permettre sa reproduction.

---

# 1. Contexte du projet

**BookWorld** est une entreprise fictive spécialisée dans la vente de livres en ligne.

Les données utiles sont dispersées entre plusieurs sources :

- un fichier CSV contenant les ventes brutes ;
- une base SQLite contenant les référentiels métier ;
- le site [BooksToScrape](https://books.toscrape.com/) contenant les informations du catalogue ;
- l’API publique Frankfurter permettant de récupérer le taux de change GBP → EUR.

Le but est de centraliser ces données dans un pipeline reproductible puis de construire un indicateur final de ventes par pays.

La table finale principale s’appelle :

```text
sales_by_country
```

Elle contient :

- `country_code`
- `country_name`
- `total_orders`
- `total_quantity`
- `total_revenue_gbp`
- `total_revenue_eur`

---

# 2. Architecture générale

Le projet suit une logique ETL simple :

```text
SOURCES
   │
   ├── sales_raw.csv
   ├── bookworld_reference.db
   ├── BooksToScrape — première page
   └── API Frankfurter
   │
   ▼
EXTRACT
   │
   ▼
TRANSFORM
   │
   ├── nettoyage
   ├── correspondances
   ├── enrichissements
   ├── calculs de revenus
   └── agrégation par pays
   │
   ▼
LOAD
   │
   ▼
business_data.db
   │
   ▼
sales_by_country
   │
   ▼
API REST Flask
```

Le fichier principal du pipeline est `pipeline.py`.

Le fichier `api.py` expose les données finales avec Flask.

---

# 3. Structure du projet

```text
BookWorld/
│
├── sales_raw.csv
├── bookworld_reference.db
├── business_data.db
├── pipeline.py
├── api.py
├── queries.sql
├── schema_final.sql
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

## Rôle des fichiers

### `pipeline.py`

Contient le pipeline principal : lecture des données, extraction des sources externes, nettoyage, enrichissement, calcul des revenus, agrégation et alimentation de la base finale.

### `api.py`

Contient l’API REST Flask et expose notamment :

```text
GET /health
GET /sales-by-country
```

### `queries.sql`

Contient les requêtes SQL utilisées dans le projet, notamment une requête avec filtre et une requête utile à l’enrichissement du pipeline.

### `schema_final.sql`

Définit la structure de la base finale et de la table `sales_by_country`.

### `business_data.db`

Base SQLite finale créée et alimentée par le pipeline.

### `.env`

Contient localement le token utilisé pour protéger l’endpoint métier de l’API.

Ce fichier ne doit jamais être publié sur GitHub.

### `.env.example`

Fichier modèle pouvant être versionné :

```text
BOOKWORLD_API_TOKEN=your_token_here
```

### `.gitignore`

Permet notamment d’exclure :

```text
.env
__pycache__/
*.pyc
```

---

# 4. Prérequis

Il faut disposer de :

- Python ;
- pip ;
- Git ;
- un terminal ;
- un compte GitHub pour accéder au dépôt du projet.

Vérifier les installations :

```bash
python --version
pip --version
git --version
```

---

# 5. Récupérer le projet

Le dépôt GitHub du projet est :

```text
https://github.com/mrlaurentmike-a11y/BookWorld.git
```

Pour récupérer le projet :

```bash
git clone https://github.com/mrlaurentmike-a11y/BookWorld.git
cd BookWorld
```

---

# 6. Installer les dépendances

Les principales bibliothèques utilisées sont :

- pandas
- requests
- beautifulsoup4
- flask
- python-dotenv

Installation :

```bash
pip install -r requirements.txt
```

---

# 7. Sources de données

## 7.1 CSV — `sales_raw.csv`

Le fichier contient les données brutes des ventes.

Les informations utilisées comprennent notamment :

```text
order_id
order_date
book_id
country_code
channel_code
quantity
discount_rate
book_name
```

Le fichier contient également `customer_first_name` et `customer_last_name`. Ces données personnelles ne sont pas conservées dans la base finale car elles ne sont pas nécessaires à l’objectif d’agrégation par pays.

## 7.2 Base SQLite — `bookworld_reference.db`

La base de référence contient notamment les tables :

```text
countries
channels
category_rules
```

Le référentiel `countries` est utilisé pour enrichir les ventes avec le nom du pays.

Un cas d’incohérence a été identifié : `NL` apparaît dans les ventes mais n’existe pas dans le référentiel `countries`.

La règle retenue est de conserver `country_code = NL` et d’utiliser `country_name = "Unknown"` plutôt que d’inventer une correspondance.

## 7.3 Scraping de BooksToScrape

Le scraping est limité à la première page du site :

```text
https://books.toscrape.com/
```

Les informations utilisées comprennent notamment le titre et le prix du livre.

Les 20 livres de cette première page correspondent aux livres présents dans les ventes du projet.

## 7.4 API Frankfurter

L’API publique Frankfurter est utilisée pour récupérer le taux de change GBP → EUR.

Le taux est utilisé pour calculer `revenue_eur` à partir du revenu en GBP.

Les montants en EUR peuvent donc varier selon le taux récupéré au moment de l’exécution du pipeline.

---

# 8. Contrôles qualité des données

Plusieurs contrôles ont été réalisés avant la consolidation :

- 240 lignes de ventes ;
- 240 `order_id` uniques ;
- aucune valeur manquante détectée dans les données brutes auditées ;
- aucun doublon exact détecté ;
- 20 livres différents présents dans les ventes ;
- 3 canaux présents dans les ventes ;
- contrôle des correspondances entre les différentes sources ;
- contrôle de l’unicité des `country_code` dans l’agrégation finale.

Une attention particulière a été portée aux jointures afin d’éviter de multiplier les lignes lors des enrichissements.

---

# 9. Exécuter le pipeline

Depuis la racine du projet :

```bash
python pipeline.py
```

Le pipeline :

1. lit les données de ventes ;
2. extrait les référentiels SQLite nécessaires ;
3. récupère les données de la première page de BooksToScrape ;
4. récupère le taux GBP → EUR via Frankfurter ;
5. nettoie et enrichit les données ;
6. calcule les revenus ;
7. produit `sales_by_country` ;
8. crée et alimente `business_data.db`.

---

# 10. Calcul des revenus

Le revenu en GBP est calculé à partir du prix, de la quantité et de la remise :

```text
revenue_gbp = price_gbp × quantity × (1 - discount_rate)
```

Le revenu en EUR est ensuite calculé avec le taux GBP → EUR récupéré auprès de Frankfurter :

```text
revenue_eur = revenue_gbp × taux_GBP_EUR
```

Les montants sont arrondis à deux décimales.

---

# 11. Agrégation finale

Le pipeline produit la table :

```text
sales_by_country
```

L’agrégation contient :

```text
country_code
country_name
total_orders
total_quantity
total_revenue_gbp
total_revenue_eur
```

Les données sont regroupées par pays.

---

# 12. Base finale

Le fichier final est :

```text
business_data.db
```

Il contient la table :

```text
sales_by_country
```

La structure est définie dans `schema_final.sql`.

`country_code` est la clé primaire.

Les autres colonnes sont définies comme obligatoires (`NOT NULL`).

---

# 13. RGPD et minimisation des données

Le fichier de ventes brutes contient les colonnes :

```text
customer_first_name
customer_last_name
```

Ces informations ne sont pas nécessaires pour produire les ventes agrégées par pays.

Elles ne sont donc pas conservées dans la base finale.

Le projet applique ainsi un principe simple de minimisation : ne conserver que les données nécessaires à l’objectif du traitement.

---

# 14. Variables d’environnement et token API

Créer un fichier `.env` à la racine du projet :

```text
BOOKWORLD_API_TOKEN=your_token_here
```

Le vrai token utilisé localement doit rester dans `.env` et ne doit pas être publié sur GitHub.

Le fichier `.env.example` sert uniquement de modèle.

L’API utilise un en-tête HTTP de type Bearer :

```text
Authorization: Bearer <token>
```

---

# 15. Lancer l’API

Après avoir exécuté le pipeline :

```bash
python api.py
```

Adresse locale :

```text
http://127.0.0.1:5000
```

---

# 16. Endpoints disponibles

## `GET /health`

Permet de vérifier que l’API fonctionne.

Exemple :

```text
http://127.0.0.1:5000/health
```

Réponse attendue :

```json
{
  "status": "ok"
}
```

Cette route est accessible sans token.

## `GET /sales-by-country`

Retourne les ventes agrégées par pays.

Cette route nécessite un Bearer token valide.

En-tête attendu :

```text
Authorization: Bearer <token>
```

Les champs retournés sont :

```text
country_code
country_name
total_orders
total_quantity
total_revenue_gbp
total_revenue_eur
```

---

# 17. Tester l’API

Les tests suivants ont été réalisés avec succès.

## Tester `/health`

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Résultat attendu :

```text
status
------
ok
```

## Tester `/sales-by-country` sans token

```powershell
Invoke-RestMethod http://127.0.0.1:5000/sales-by-country
```

Résultat attendu :

```json
{
  "error": "Unauthorized"
}
```

Code HTTP : `401 Unauthorized`.

## Tester avec un token valide

```powershell
$headers = @{
    Authorization = "Bearer <token>"
}

Invoke-RestMethod `
    -Uri http://127.0.0.1:5000/sales-by-country `
    -Headers $headers
```

L’API doit retourner les ventes agrégées par pays.

## Tester avec un mauvais token

```powershell
$badHeaders = @{
    Authorization = "Bearer mauvais-token"
}

Invoke-RestMethod `
    -Uri http://127.0.0.1:5000/sales-by-country `
    -Headers $badHeaders
```

Résultat attendu :

```json
{
  "error": "Unauthorized"
}
```

Code HTTP : `401 Unauthorized`.

---

# 18. Sécurité

L’authentification par Bearer token est adaptée à ce projet pédagogique mais reste simple.

Points appliqués dans le projet :

- le token n’est pas écrit en clair dans `api.py` ;
- le token local est stocké dans `.env` ;
- `.env` est exclu par `.gitignore` ;
- `.env.example` ne contient pas le vrai token ;
- `/health` reste accessible sans authentification ;
- `/sales-by-country` est protégé par token.

Dans un environnement de production, des mécanismes de sécurité plus complets seraient nécessaires.

---

# 19. Dépannage

## `ModuleNotFoundError`

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Erreur `401 Unauthorized`

Vérifier :

- que `.env` existe à la racine du projet ;
- que `BOOKWORLD_API_TOKEN` est correctement défini ;
- que le token envoyé correspond au token local ;
- que l’en-tête respecte la forme `Authorization: Bearer <token>`.

## Base SQLite indisponible

Vérifier que `business_data.db` existe et que `pipeline.py` a bien été exécuté.

## Problème de données EUR

Le taux GBP → EUR est récupéré depuis une API externe au moment de l’exécution. Vérifier la connexion internet et la disponibilité du service Frankfurter.

---

# 20. Git et GitHub

Le projet est versionné avec Git et publié sur GitHub.

Dépôt :

```text
https://github.com/mrlaurentmike-a11y/BookWorld.git
```

Le projet utilise la branche :

```text
main
```

L’authentification GitHub utilisée pour la publication du projet est HTTPS.

Le token de l’API BookWorld reste distinct de l’authentification utilisée pour GitHub.

---

# 21. Vérifications avant de rendre le projet

- [x] le pipeline s’exécute ;
- [x] les dépendances sont documentées ;
- [x] `requirements.txt` est présent ;
- [x] `README.md` est présent ;
- [x] `queries.sql` est présent ;
- [x] `schema_final.sql` est présent ;
- [x] `api.py` fonctionne ;
- [x] `/health` fonctionne ;
- [x] `/sales-by-country` fonctionne avec authentification ;
- [x] le token n’est pas publié ;
- [x] `.env` est dans `.gitignore` ;
- [x] les noms et prénoms ne sont pas présents dans la base finale ;
- [x] le projet est publié sur GitHub.

À compléter pour la remise finale :

- [ ] rapport RNCP ;
- [ ] intégrer au rapport la capture du schéma de la base ;
- [ ] vérifier une dernière fois la conformité du dépôt avec les consignes du formateur.

---

# 22. Limites du projet

- données fictives ;
- scraping limité à la première page ;
- dépendance à des services externes ;
- authentification API simple ;
- SQLite adapté à un projet de petite taille ;
- serveur Flask de développement.

---

# 23. Pistes d’amélioration

- automatiser les tests ;
- ajouter des logs ;
- améliorer la gestion des erreurs et des reprises sur les API externes ;
- renforcer l’authentification ;
- ajouter une documentation API plus détaillée ;
- utiliser une base de données adaptée à un environnement de production si nécessaire ;
- déployer l’API.

---

# 24. Résumé

```text
CSV
+
SQLite
+
Scraping BooksToScrape
+
API Frankfurter
        ↓
     Pipeline
        ↓
Nettoyage / Enrichissement
        ↓
   Agrégation par pays
        ↓
   business_data.db
        ↓
      API Flask
```

Le projet permet de passer de plusieurs sources de données à une base SQLite finale puis à une API REST simple.

Le README doit permettre à une personne qui ne connaît pas le projet de comprendre :

1. à quoi sert le projet ;
2. quelles sources sont utilisées ;
3. comment installer les dépendances ;
4. comment exécuter le pipeline ;
5. comment lancer et tester l’API ;
6. comment protéger le token ;
7. comment reproduire le projet.
