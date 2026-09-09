import os
import sqlite3

from dotenv import load_dotenv
from flask import Flask
from flask import request

load_dotenv()

app = Flask(__name__)

API_TOKEN = os.getenv("BOOKWORLD_API_TOKEN")


def check_token():
    """Vérifie le token d'authentification."""
    auth_header = request.headers.get("Authorization")

    if auth_header != f"Bearer {API_TOKEN}":
        return False

    return True


def get_db_connection():
    """Ouvre une connexion vers la base finale."""
    connection = sqlite3.connect("business_data.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/health", methods=["GET"])
def health():
    """Vérifie que l'API fonctionne."""
    return {"status": "ok"}


@app.route("/sales-by-country", methods=["GET"])
def sales_by_country():
    """Retourne les ventes agrégées par pays."""

    if not check_token():
        return {"error": "Unauthorized"}, 401

    connection = get_db_connection()

    rows = connection.execute(
        "SELECT * FROM sales_by_country"
    ).fetchall()

    connection.close()

    results = []

    for row in rows:
        data = dict(row)
        data["total_revenue_gbp"] = round(data["total_revenue_gbp"], 2)
        data["total_revenue_eur"] = round(data["total_revenue_eur"], 2)
        results.append(data)

    return results


if __name__ == "__main__":
    app.run(debug=True)