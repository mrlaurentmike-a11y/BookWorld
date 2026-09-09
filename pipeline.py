import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup


# ============================================================
# 1. Extraction des ventes
# ============================================================

def extract_sales():
    """Lit le fichier CSV des ventes."""

    try:
        # Lecture du fichier CSV contenant les ventes brutes
        sales = pd.read_csv("sales_raw.csv")

        # Contrôles simples pour vérifier les données récupérées
        print("Nombre de ventes :", len(sales))
        print("Colonnes des ventes :", sales.columns.tolist())

        # Retourne le DataFrame contenant les ventes
        return sales

    except FileNotFoundError:
        # Cette erreur se produit si le fichier CSV n'existe pas
        print("Erreur : le fichier sales_raw.csv est introuvable.")
        return None

    except Exception as error:
        # Gestion des autres erreurs éventuelles lors de la lecture du fichier
        print(f"Erreur lors de la lecture du CSV : {error}")
        return None


# ============================================================
# 2. Extraction des données de référence
# ============================================================

def extract_countries():
    """Extrait les données des pays depuis la base SQLite."""

    try:
        # Ouvre une connexion vers la base SQLite de référence
        conn = sqlite3.connect("bookworld_reference.db")

        # Récupère toutes les données de la table countries
        countries = pd.read_sql_query(
            "SELECT * FROM countries",
            conn
        )

        # Ferme la connexion une fois les données récupérées
        conn.close()

        # Contrôles simples pour vérifier les données récupérées
        print("Nombre de pays :", len(countries))
        print("Colonnes des pays :", countries.columns.tolist())

        # Retourne le DataFrame contenant les pays
        return countries

    except sqlite3.Error as error:
        # Gestion des erreurs liées à SQLite
        print(f"Erreur lors de la lecture de SQLite : {error}")
        return None


# ============================================================
# 3. Scraping du catalogue
# ============================================================

def scrape_books():
    """Récupère les livres de la première page de BooksToScrape."""

    # URL de la première page du catalogue
    url = "https://books.toscrape.com/"

    try:
        # Envoie une requête vers le site
        response = requests.get(url)

        # Déclenche une erreur si le serveur retourne un code HTTP d'erreur
        response.raise_for_status()

        # Affiche le code HTTP reçu
        print("Statut BooksToScrape :", response.status_code)

        # Transforme le HTML reçu en objet exploitable avec BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Liste qui va contenir les informations des livres
        books = []

        # Recherche tous les blocs correspondant aux livres
        livres = soup.find_all(
            "article",
            class_="product_pod"
        )

        # Parcourt chaque livre trouvé sur la page
        for livre in livres:

            # Récupère le titre du livre
            title = livre.find("h3").find("a")["title"]

            # Récupère le prix affiché sur le site
            price = livre.find(
                "p",
                class_="price_color"
            ).get_text(strip=True)

            # Récupère la disponibilité du livre
            availability = livre.find(
                "p",
                class_="instock availability"
            ).get_text(strip=True)

            # Ajoute les informations du livre dans la liste
            books.append({
                "book_name": title,
                "price_gbp": price,
                "availability": availability
            })

        # Contrôle du nombre de livres récupérés
        print("Nombre de livres :", len(books))

        # Retourne la liste des livres
        return books

    except requests.RequestException as error:
        # Gestion des erreurs liées à la requête HTTP
        print(f"Erreur lors de l'accès à BooksToScrape : {error}")
        return None

    except Exception as error:
        # Gestion des autres erreurs éventuelles pendant le scraping
        print(f"Erreur lors du scraping : {error}")
        return None


# ============================================================
# 4. Récupération du taux de change
# ============================================================

def get_exchange_rate():
    """Récupère le taux de change GBP vers EUR."""

    # URL de l'API Frankfurter pour récupérer le taux GBP → EUR
    url = "https://api.frankfurter.dev/v2/rate/GBP/EUR"

    try:
        # Envoie une requête vers l'API
        response = requests.get(url)

        # Vérifie que la requête s'est correctement déroulée
        response.raise_for_status()

        # Affiche le code HTTP reçu
        print("Statut Frankfurter :", response.status_code)

        # Convertit la réponse JSON en dictionnaire Python
        exchange_data = response.json()

        # Récupère uniquement la valeur du taux de change
        rate = exchange_data["rate"]

        # Affiche le taux récupéré
        print("Taux GBP/EUR :", rate)

        # Retourne le taux de change
        return rate

    except requests.RequestException as error:
        # Gestion des erreurs liées à la connexion à l'API
        print(f"Erreur lors de l'accès à Frankfurter : {error}")
        return None

    except (KeyError, ValueError) as error:
        # Gestion des erreurs si la réponse JSON n'a pas le format attendu
        print(f"Erreur dans la réponse de Frankfurter : {error}")
        return None


# ============================================================
# 5. Chargement dans la base finale
# ============================================================

def load_final_database(sales_by_country):
    """Crée et alimente la base finale."""

    # Ouvre une connexion vers la base finale
    connection = sqlite3.connect("business_data.db")

    # Lit le script SQL contenant la structure de la table finale
    with open("schema_final.sql", "r", encoding="utf-8") as file:
        schema = file.read()

    # Supprime l'ancienne table si elle existe déjà
    connection.execute("DROP TABLE IF EXISTS sales_by_country;")

    # Crée la table à partir du fichier schema_final.sql
    connection.executescript(schema)

    # Insère les données agrégées dans la table finale
    sales_by_country.to_sql(
        "sales_by_country",
        connection,
        if_exists="append",
        index=False
    )

    # Ferme la connexion à la base
    connection.close()

    print("\nBase finale créée et alimentée.")


# ============================================================
# 6. Exécution du pipeline
# ============================================================

def main():
    """Exécute les différentes étapes du pipeline."""

    # --------------------------------------------------------
    # Extraction des différentes sources
    # --------------------------------------------------------

    # Récupère les ventes depuis le fichier CSV
    sales = extract_sales()

    # Récupère le référentiel des pays depuis SQLite
    countries = extract_countries()

    # Récupère les livres depuis la première page de BooksToScrape
    books = scrape_books()

    # Transforme la liste de livres en DataFrame Pandas
    books = pd.DataFrame(books)

    # --------------------------------------------------------
    # Nettoyage du prix des livres
    # --------------------------------------------------------

    # Supprime le symbole £ et transforme le prix en nombre
    books["price_gbp"] = (
        books["price_gbp"]
        .str.replace("Â£", "", regex=False)
        .astype(float)
    )

    print("\nAperçu des prix :")
    print(books[["book_name", "price_gbp"]].head())

    # --------------------------------------------------------
    # Enrichissement des ventes avec le prix des livres
    # --------------------------------------------------------

    # Ajoute le prix du livre aux ventes grâce au nom du livre
    sales = sales.merge(
        books[["book_name", "price_gbp"]],
        on="book_name",
        how="left"
    )

    print("\nAperçu des ventes avec le prix :")
    print(
        sales[
            [
                "book_name",
                "price_gbp",
                "quantity",
                "discount_rate"
            ]
        ].head(10)
    )

    # --------------------------------------------------------
    # Calcul du revenu en GBP
    # --------------------------------------------------------

    # Calcule le revenu en tenant compte de la quantité
    # et de la remise appliquée à chaque vente
    sales["revenue_gbp"] = (
        sales["price_gbp"]
        * sales["quantity"]
        * (1 - sales["discount_rate"])
    )

    # Arrondit le revenu à deux décimales
    sales["revenue_gbp"] = sales["revenue_gbp"].round(2)

    print("\nAperçu du revenue_gbp :")
    print(
        sales[
            [
                "book_name",
                "price_gbp",
                "quantity",
                "discount_rate",
                "revenue_gbp"
            ]
        ].head(10)
    )

    # --------------------------------------------------------
    # Conversion du revenu en EUR
    # --------------------------------------------------------

    # Récupère le taux de change GBP → EUR
    exchange_rate = get_exchange_rate()

    # Convertit le revenu GBP en EUR
    sales["revenue_eur"] = sales["revenue_gbp"] * exchange_rate

    # Arrondit le revenu en EUR à deux décimales
    sales["revenue_eur"] = sales["revenue_eur"].round(2)

    print("\nAperçu du revenue_eur :")
    print(
        sales[
            [
                "book_name",
                "revenue_gbp",
                "revenue_eur"
            ]
        ].head(10)
    )

    # --------------------------------------------------------
    # Enrichissement avec le référentiel des pays
    # --------------------------------------------------------

    # Ajoute les informations du référentiel countries
    # grâce au code pays
    sales = sales.merge(
        countries,
        on="country_code",
        how="left"
    )

    # Remplace les pays sans correspondance par "Unknown"
    # afin de conserver les ventes concernées
    sales["country_name"] = sales["country_name"].fillna("Unknown")

    print("\nAperçu des ventes avec les informations pays :")
    print(
        sales[
            [
                "country_code",
                "country_name",
                "currency_code",
                "vat_rate",
                "region",
                "is_active"
            ]
        ].head(10)
    )

    # Vérifie quels codes pays n'ont pas de correspondance
    print("\nCodes pays sans correspondance :")
    print(
        sales.loc[
            sales["country_name"] == "Unknown",
            "country_code"
        ].unique()
    )

    # --------------------------------------------------------
    # Agrégation finale par pays
    # --------------------------------------------------------

    # Regroupe les ventes par code et nom du pays
    sales_by_country = (
        sales
        .groupby(
            ["country_code", "country_name"],
            as_index=False
        )
        .agg(
            # Nombre de commandes / ventes
            total_orders=("order_id", "count"),

            # Quantité totale vendue
            total_quantity=("quantity", "sum"),

            # Chiffre d'affaires total en GBP
            total_revenue_gbp=("revenue_gbp", "sum"),

            # Chiffre d'affaires total en EUR
            total_revenue_eur=("revenue_eur", "sum")
        )
    )

    print("\nColonnes de sales_by_country :")
    print(sales_by_country.columns.tolist())

    # Colonnes attendues dans la table finale
    expected_columns = [
        "country_code",
        "country_name",
        "total_orders",
        "total_quantity",
        "total_revenue_gbp",
        "total_revenue_eur"
    ]

    # Vérifie que les colonnes obtenues correspondent
    # exactement aux colonnes attendues
    print("\nLes colonnes sont-elles correctes ?")
    print(sales_by_country.columns.tolist() == expected_columns)

    print("\nAperçu de sales_by_country :")
    print(sales_by_country)

    # --------------------------------------------------------
    # Contrôles sur les codes pays
    # --------------------------------------------------------

    # Vérifie qu'un même country_code ne correspond pas
    # à plusieurs country_name
    print("\nVérification de l'unicité des country_code :")
    print(
        sales_by_country.groupby("country_code")["country_name"]
        .nunique()
    )

    # Recherche les éventuels country_code présents plusieurs fois
    print("\nCodes pays présents plusieurs fois :")
    print(
        sales_by_country[
            sales_by_country.duplicated(
                subset=["country_code"],
                keep=False
            )
        ]
    )

    # Vérifie le nombre total de lignes dans l'agrégation finale
    print("\nNombre de lignes dans sales_by_country :")
    print(len(sales_by_country))

    # Vérifie le nombre de codes pays uniques
    print("\nNombre de country_code uniques :")
    print(sales_by_country["country_code"].nunique())

    # --------------------------------------------------------
    # Chargement de la base finale
    # --------------------------------------------------------

    # Crée et alimente business_data.db
    # avec les données agrégées par pays
    load_final_database(sales_by_country)

    print("\nPipeline terminé.")


# ============================================================
# Point d'entrée du programme
# ============================================================

# Lance la fonction main() uniquement lorsque
# ce fichier est exécuté directement
if __name__ == "__main__":
    main()