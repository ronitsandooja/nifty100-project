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

load_stats = []


def get_header(dataset_name):
    if dataset_name in core_files:
        return 1
    return 0


def load_all_datasets(base_path="data/raw"):
    base = Path(base_path)

    datasets = {}

    for file in base.glob("*.xlsx"):
        name = file.stem.lower()

        try:
            df = load_dataset(str(file))
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


def process_df(df):
    df = clean_columns(df)
    df = remove_empty_rows(df)
    df = clean_text_columns(df)

    df = normalize_ticker_column(df, "company_id")
    df = normalize_ticker_column(df, "id")
    df = normalize_year_column(df, "year")

    df = remove_duplicates(df)

    return df


def load_dataset(file_path):
    path = Path(file_path)
    dataset_name = path.stem.lower()

    header = get_header(dataset_name)

    df = pd.read_excel(
        path,
        header=header,
        engine="openpyxl"
    )

    rows_before = len(df)

    df = process_df(df)

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


def preview(df):
    print(df.head())


if __name__ == "__main__":
    df = load_dataset("data/raw/companies.xlsx")
    preview(df)
    save_load_stats()
