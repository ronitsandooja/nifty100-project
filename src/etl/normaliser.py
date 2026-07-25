import re
from datetime import datetime
import pandas as pd


# basic cleaning helpers

def normalize_ticker(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()
    return value if value else None


def clean_text(value):
    if pd.isna(value):
        return None

    value = str(value)
    value = value.replace("\n", " ").strip()

    return value if value else None


def to_float(value):
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value)
    value = value.replace(",", "").replace("%", "").strip()

    if value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


# year handling

def normalize_year(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    # already formatted
    if re.match(r"^\d{4}-\d{2}$", value):
        return value

    # common formats
    formats = ["%b-%y", "%b %y", "%B-%Y", "%B %Y", "%b-%Y", "%b %Y"]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m")
        except ValueError:
            continue

    # FY format
    fy = re.match(r"FY(\d{4})", value.upper())
    if fy:
        return f"{fy.group(1)}-03"

    fy = re.match(r"FY(\d{2})", value.upper())
    if fy:
        yr = int(fy.group(1))
        yr = 2000 + yr if yr <= 30 else 1900 + yr
        return f"{yr}-03"

    # plain year
    if re.match(r"^\d{4}$", value):
        return f"{value}-03"

    return None


# dataframe helpers

def clean_text_columns(df):
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].apply(clean_text)
    return df


def normalize_ticker_column(df, col):
    if col in df.columns:
        df[col] = df[col].apply(normalize_ticker)
    return df


def normalize_year_column(df, col):
    if col in df.columns:
        df[col] = df[col].apply(normalize_year)
    return df


def convert_numeric_column(df, col):
    if col in df.columns:
        df[col] = df[col].apply(to_float)
    return df


def remove_empty_rows(df):
    return df.dropna(how="all")
