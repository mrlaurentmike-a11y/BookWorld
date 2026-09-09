CREATE TABLE sales_by_country (
    country_code TEXT PRIMARY KEY,
    country_name TEXT NOT NULL,
    total_orders INTEGER NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_revenue_gbp REAL NOT NULL,
    total_revenue_eur REAL NOT NULL
);