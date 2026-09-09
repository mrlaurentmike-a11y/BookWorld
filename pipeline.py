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
        sales = pd.read_csv("sales_raw.csv")

        print("Nombre de ventes :", len(sales))
        print("Colonnes des ventes :", sales.columns.tolist())

        return sales

    except FileNotFoundError:
        print("Erreur : le fichier sales_raw.csv est introuvable.")
        return None

    except Exception as error:
        print(f"Erreur lors de la lecture du CSV : {error}")
        return None


# ============================================================
# 2. Extraction des données de référence
# ============================================================

def extract_countries():
    """Extrait les données des pays depuis la base SQLite."""

    try:
        conn = sqlite3.connect("bookworld_reference.db")

        countries = pd.read_sql_query(
            "SELECT * FROM countries",
            conn
        )

        conn.close()

        print("Nombre de pays :", len(countries))
        print("Colonnes des pays :", countries.columns.tolist())

        return countries

    except sqlite3.Error as error:
        print(f"Erreur lors de la lecture de SQLite : {error}")
        return None


# ============================================================
# 3. Scraping du catalogue
# ============================================================

def scrape_books():
    """Récupère les livres de la première page de BooksToScrape."""

    url = "https://books.toscrape.com/"

    try:
        response = requests.get(url)
        response.raise_for_status()

        print("Statut BooksToScrape :", response.status_code)

        soup = BeautifulSoup(response.text, "html.parser")

        books = []

        livres = soup.find_all(
            "article",
            class_="product_pod"
        )

        for livre in livres:

            title = livre.find("h3").find("a")["title"]

            price = livre.find(
                "p",
                class_="price_color"
            ).get_text(strip=True)

            availability = livre.find(
                "p",
                class_="instock availability"
            ).get_text(strip=True)

            books.append({
                "book_name": title,
                "price_gbp": price,
                "availability": availability
            })

        print("Nombre de livres :", len(books))

        return books

    except requests.RequestException as error:
        print(f"Erreur lors de l'accès à BooksToScrape : {error}")
        return None

    except Exception as error:
        print(f"Erreur lors du scraping : {error}")
        return None

# ============================================================
# 4. Récupération du taux de change
# ============================================================

def get_exchange_rate():
    """Récupère le taux de change GBP vers EUR."""

    url = "https://api.frankfurter.dev/v2/rate/GBP/EUR"

    try:
        response = requests.get(url)
        response.raise_for_status()

        print("Statut Frankfurter :", response.status_code)

        exchange_data = response.json()

        rate = exchange_data["rate"]

        print("Taux GBP/EUR :", rate)

        return rate

    except requests.RequestException as error:
        print(f"Erreur lors de l'accès à Frankfurter : {error}")
        return None

    except (KeyError, ValueError) as error:
        print(f"Erreur dans la réponse de Frankfurter : {error}")
        return None


def load_final_database(sales_by_country):
    """Crée et alimente la base finale."""

    connection = sqlite3.connect("business_data.db")

    with open("schema_final.sql", "r", encoding="utf-8") as file:
        schema = file.read()

    connection.execute("DROP TABLE IF EXISTS sales_by_country;")
    connection.executescript(schema)

    sales_by_country.to_sql(
        "sales_by_country",
        connection,
        if_exists="append",
        index=False
    )

    connection.close()

    print("\nBase finale créée et alimentée.")


# ============================================================
# 5. Exécution du pipeline
# ============================================================

def main():
    """Exécute les différentes étapes d'extraction."""

    sales = extract_sales()
    countries = extract_countries()
    books = scrape_books()
    books = pd.DataFrame(books)

    books["price_gbp"] = (
        books["price_gbp"]
        .str.replace("Â£", "", regex=False)
        .astype(float)
    )

    print("\nAperçu des prix :")
    print(books[["book_name", "price_gbp"]].head())

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

    sales["revenue_gbp"] = (
        sales["price_gbp"]
        * sales["quantity"]
        * (1 - sales["discount_rate"])
    )

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

    exchange_rate = get_exchange_rate()

    sales["revenue_eur"] = sales["revenue_gbp"] * exchange_rate
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

    sales = sales.merge(
        countries,
        on="country_code",
        how="left"
    )

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

    print("\nCodes pays sans correspondance :")
    print(
        sales.loc[
            sales["country_name"] == "Unknown",
            "country_code"
        ].unique()
    )

    sales_by_country = (
        sales
        .groupby(
            ["country_code", "country_name"],
            as_index=False
        )
        .agg(
            total_orders=("order_id", "count"),
            total_quantity=("quantity", "sum"),
            total_revenue_gbp=("revenue_gbp", "sum"),
            total_revenue_eur=("revenue_eur", "sum")
        )
    )

    print("\nColonnes de sales_by_country :")
    print(sales_by_country.columns.tolist())

    expected_columns = [
        "country_code",
        "country_name",
        "total_orders",
        "total_quantity",
        "total_revenue_gbp",
        "total_revenue_eur"
    ]

    print("\nLes colonnes sont-elles correctes ?")
    print(sales_by_country.columns.tolist() == expected_columns)

    print("\nAperçu de sales_by_country :")
    print(sales_by_country)

    # Vérification de l'unicité des country_code
    print("\nVérification de l'unicité des country_code :")
    print(
        sales_by_country.groupby("country_code")["country_name"]
        .nunique()
    )

    # Vérification des doublons de country_code
    print("\nCodes pays présents plusieurs fois :")
    print(
        sales_by_country[
            sales_by_country.duplicated(
                subset=["country_code"],
                keep=False
            )
        ]
    )

    # Vérification du nombre de lignes et de codes pays uniques
    print("\nNombre de lignes dans sales_by_country :")
    print(len(sales_by_country))

    print("\nNombre de country_code uniques :")
    print(sales_by_country["country_code"].nunique())

    load_final_database(sales_by_country)

    print("\nExtraction terminée.")


if __name__ == "__main__":
    main()











