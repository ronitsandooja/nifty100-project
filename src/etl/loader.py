import sqlite3
import pandas as pd
from pathlib import Path

from src.etl.normaliser import (
    clean_text_columns,
    normalize_ticker_column,
    normalize_year_column,
    remove_empty_rows
)


core_files = {
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons"
}

table_order = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "stock_prices"
]

load_stats = []


def get_header(dataset_name):
    if dataset_name in core_files:
        return 1
    return 0


def load_all_datasets(raw_path="data/raw", supporting_path="data/supporting"):
    raw_base = Path(raw_path)
    supporting_base = Path(supporting_path)

    datasets = {}

    companies_path = raw_base / "companies.xlsx"
    datasets["companies"] = load_dataset(str(companies_path))
    valid_ids = set(datasets["companies"]["id"].dropna())

    files = list(raw_base.glob("*.xlsx")) + list(supporting_base.glob("*.xlsx"))

    for file in files:
        name = file.stem.lower()

        if name == "companies":
            continue

        try:
            df = load_dataset(str(file), valid_ids)
            datasets[name] = df
        except Exception as e:
            print(f"error loading {name}: {e}")

    return datasets

def clean_columns(df):
    cols = []

    for col in df.columns:
        col = str(col)
        col = col.strip().lower()
        col = col.replace(" ", "_")
        col = col.replace("%", "percentage")
        cols.append(col)

    df.columns = cols
    return df


def remove_duplicates(df):
    if "company_id" in df.columns and "year" in df.columns:
        df = df.drop_duplicates(
            subset=["company_id", "year"],
            keep="last"
        )
    return df


def drop_bad_years(df):
    if "year" in df.columns:
        df = df[df["year"].notna()]
    return df


def drop_orphan_rows(df, valid_ids):
    if valid_ids is not None and "company_id" in df.columns:
        df = df[df["company_id"].isin(valid_ids)]
    return df


def process_df(df, valid_ids=None):
    df = clean_columns(df)
    df = remove_empty_rows(df)
    df = clean_text_columns(df)

    df = normalize_ticker_column(df, "company_id")
    df = normalize_ticker_column(df, "id")
    df = normalize_year_column(df, "year")

    df = drop_bad_years(df)
    df = drop_orphan_rows(df, valid_ids)

    df = remove_duplicates(df)

    return df


def load_dataset(file_path, valid_ids=None):
    path = Path(file_path)
    dataset_name = path.stem.lower()

    header = get_header(dataset_name)

    df = pd.read_excel(
        path,
        header=header,
        engine="openpyxl"
    )

    rows_before = len(df)

    df = process_df(df, valid_ids)

    rows_after = len(df)

    load_stats.append({
        "table_name": dataset_name,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rejected_rows": rows_before - rows_after
    })

    print(f"{dataset_name} -> {rows_after} rows")

    return df


def save_load_stats():
    stats_df = pd.DataFrame(load_stats)
    stats_df.to_csv("output/load_audit.csv", index=False)


def build_database(datasets, db_path="db/nifty100.db"):
    conn = sqlite3.connect(db_path)

    with open("db/drop_tables.sql") as f:
        conn.executescript(f.read())

    with open("db/schema.sql") as f:
        conn.executescript(f.read())

    for name in table_order:
        datasets[name].to_sql(name, conn, if_exists="append", index=False)

    conn.execute("pragma foreign_keys = on")
    fk_errors = conn.execute("pragma foreign_key_check").fetchall()

    conn.commit()
    conn.close()

    return fk_errors


def preview(df):
    print(df.head())


if __name__ == "__main__":
    datasets = load_all_datasets()
    save_load_stats()

    fk_errors = build_database(datasets)
    print("fk errors:", len(fk_errors))
