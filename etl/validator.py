import os
import re
import pandas as pd


validation_results = []


def add_failure(rule_id, company_id, year, field, issue, severity):
    validation_results.append({
        "rule_id": rule_id,
        "company_id": company_id,
        "year": year,
        "field": field,
        "issue": issue,
        "severity": severity,
    })


def has_columns(df, cols):
    return all(col in df.columns for col in cols)


def get_year(row):
    if "year" in row:
        return row["year"]
    if "Year" in row:
        return row["Year"]
    return None


# pk checks

def dq01_company_pk(companies_df):
    duplicates = companies_df[companies_df["id"].duplicated(keep=False)]

    for _, row in duplicates.iterrows():
        add_failure("DQ-01", row["id"], None, "id",
                    "duplicate company id", "CRITICAL")


def dq02_annual_pk(df, table):
    if not has_columns(df, ["company_id", "year"]):
        return

    duplicates = df[df.duplicated(["company_id", "year"], keep=False)]

    for _, row in duplicates.iterrows():
        add_failure("DQ-02", row["company_id"], row["year"], table,
                    "duplicate company_id + year", "CRITICAL")


# fk checks

def dq03_fk(df, companies_df, table):
    if "company_id" not in df.columns:
        return

    valid_ids = set(companies_df["id"].dropna())
    bad = df[~df["company_id"].isin(valid_ids)]

    for _, row in bad.iterrows():
        add_failure("DQ-03", row["company_id"], get_year(row),
                    "company_id", f"fk failed in {table}", "CRITICAL")


# financial checks

def dq04_balance(bs_df):
    if not has_columns(bs_df, ["company_id", "year", "total_assets", "total_liabilities"]):
        return

    for _, r in bs_df.iterrows():
        a = r["total_assets"]
        l = r["total_liabilities"]

        if pd.isna(a) or pd.isna(l) or a == 0:
            continue

        if abs(a - l) / abs(a) >= 0.01:
            add_failure("DQ-04", r["company_id"], r["year"],
                        "balance", "bs mismatch >1%", "WARNING")


def dq05_opm(pnl_df):
    if not has_columns(pnl_df, ["company_id", "year", "sales", "operating_profit", "opm_percentage"]):
        return

    for _, r in pnl_df.iterrows():
        if pd.isna(r["sales"]) or r["sales"] == 0:
            continue

        calc = r["operating_profit"] / r["sales"] * 100
        diff = abs(calc - r["opm_percentage"])

        if diff >= 1:
            add_failure("DQ-05", r["company_id"], r["year"],
                        "opm", "opm mismatch", "WARNING")


def dq06_sales(pnl_df, sectors_df=None):
    if "sales" not in pnl_df.columns:
        return

    financial = set()

    if sectors_df is not None and has_columns(sectors_df, ["company_id", "broad_sector"]):
        financial = set(
            sectors_df[
                sectors_df["broad_sector"].str.lower().str.contains("financial", na=False)
            ]["company_id"]
        )

    for _, r in pnl_df.iterrows():
        if r["company_id"] in financial:
            continue

        if r["sales"] <= 0:
            add_failure("DQ-06", r["company_id"], r["year"],
                        "sales", "sales <= 0", "WARNING")


# format checks

def dq07_year(df, table):
    col = "year" if "year" in df.columns else "Year" if "Year" in df.columns else None
    if not col:
        return

    for _, r in df.iterrows():
        val = r[col]

        if pd.isna(val):
            add_failure("DQ-07", r.get("company_id"), None,
                        col, f"missing year {table}", "CRITICAL")
            continue

        if not re.match(r"^\d{4}-\d{2}$", str(val)):
            add_failure("DQ-07", r.get("company_id"), val,
                        col, f"invalid year {table}", "CRITICAL")


def dq08_ticker(df, table):
    col = "company_id" if "company_id" in df.columns else "id" if table == "companies" else None
    if not col:
        return

    for _, r in df.iterrows():
        t = r[col]

        if pd.isna(t):
            add_failure("DQ-08", None, get_year(r), col,
                        f"missing ticker {table}", "CRITICAL")
            continue

        fixed = str(t).strip().upper()

        if t != fixed or len(fixed) < 2 or len(fixed) > 12:
            add_failure("DQ-08", fixed, get_year(r), col,
                        f"bad ticker format {table}", "CRITICAL")


# other validations

def dq09_cash(cf_df):
    if not has_columns(cf_df, ["company_id", "year",
                              "operating_activity", "investing_activity",
                              "financing_activity", "net_cash_flow"]):
        return

    for _, r in cf_df.iterrows():
        calc = r["operating_activity"] + r["investing_activity"] + r["financing_activity"]
        if abs(calc - r["net_cash_flow"]) > 10:
            add_failure("DQ-09", r["company_id"], r["year"],
                        "cashflow", "net cash mismatch", "WARNING")


def dq10_fixed(bs_df):
    if "fixed_assets" not in bs_df.columns:
        return

    for _, r in bs_df.iterrows():
        if r["fixed_assets"] < 0:
            add_failure("DQ-10", r["company_id"], r["year"],
                        "fixed_assets", "negative value", "WARNING")


def dq11_tax(pnl_df):
    if "tax_percentage" not in pnl_df.columns:
        return

    for _, r in pnl_df.iterrows():
        if r["tax_percentage"] < 0 or r["tax_percentage"] > 60:
            add_failure("DQ-11", r["company_id"], r["year"],
                        "tax", "out of range", "WARNING")


def dq12_dividend(pnl_df):
    if "dividend_payout" not in pnl_df.columns:
        return

    for _, r in pnl_df.iterrows():
        if r["dividend_payout"] > 200:
            add_failure("DQ-12", r["company_id"], r["year"],
                        "dividend", ">200%", "WARNING")


def dq13_url(doc_df):
    if "Annual_Report" not in doc_df.columns:
        return

    for _, r in doc_df.iterrows():
        url = r["Annual_Report"]

        if pd.isna(url) or not str(url).startswith("http"):
            add_failure("DQ-13", r["company_id"], r["Year"],
                        "url", "invalid url", "WARNING")


def dq14_eps(pnl_df):
    if not has_columns(pnl_df, ["company_id", "year", "net_profit", "eps"]):
        return

    for _, r in pnl_df.iterrows():
        if r["net_profit"] > 0 and r["eps"] <= 0:
            add_failure("DQ-14", r["company_id"], r["year"],
                        "eps", "eps mismatch", "WARNING")


def dq15_balance(bs_df):
    if not has_columns(bs_df, ["company_id", "year", "total_assets", "total_liabilities"]):
        return

    bad = bs_df[bs_df["total_assets"] != bs_df["total_liabilities"]]

    for _, r in bad.iterrows():
        add_failure("DQ-15", r["company_id"], r["year"],
                    "balance", "not exact", "INFO")


def dq16_coverage(companies_df, pnl_df, bs_df, cf_df):
    ids = companies_df["id"].dropna().unique()

    for cid in ids:
        if len(pnl_df[pnl_df["company_id"] == cid]) < 5:
            add_failure("DQ-16", cid, None, "pnl", "<5 years", "WARNING")

        if len(bs_df[bs_df["company_id"] == cid]) < 5:
            add_failure("DQ-16", cid, None, "bs", "<5 years", "WARNING")

        if len(cf_df[cf_df["company_id"] == cid]) < 5:
            add_failure("DQ-16", cid, None, "cf", "<5 years", "WARNING")


# main runner

def save_report(path="output/validation_failures.csv"):
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(validation_results)
    df.to_csv(path, index=False)
    return df


def run_validation(companies, pnl, bs, cf,
                   analysis=None, documents=None, sectors=None):

    validation_results.clear()

    dq01_company_pk(companies)

    dq02_annual_pk(pnl, "pnl")
    dq02_annual_pk(bs, "bs")
    dq02_annual_pk(cf, "cf")

    dq03_fk(pnl, companies, "pnl")
    dq03_fk(bs, companies, "bs")
    dq03_fk(cf, companies, "cf")

    for name, df in {
        "analysis": analysis,
        "documents": documents,
        "sectors": sectors,
    }.items():
        if df is not None:
            dq03_fk(df, companies, name)

    dq04_balance(bs)
    dq05_opm(pnl)
    dq06_sales(pnl, sectors)

    dq07_year(pnl, "pnl")
    dq07_year(bs, "bs")
    dq07_year(cf, "cf")

    dq08_ticker(companies, "companies")

    dq09_cash(cf)
    dq10_fixed(bs)
    dq11_tax(pnl)
    dq12_dividend(pnl)

    if documents is not None:
        dq13_url(documents)

    dq14_eps(pnl)
    dq15_balance(bs)
    dq16_coverage(companies, pnl, bs, cf)

    report = save_report()

    print("validation complete:", len(report), "issues")

    return report


if __name__ == "__main__":

    from src.etl.loader import load_all_datasets

    print("running validation...")

    datasets = load_all_datasets()

    report = run_validation(
        companies=datasets["companies"],
        pnl=datasets["profitandloss"],
        bs=datasets["balancesheet"],
        cf=datasets["cashflow"],
        analysis=datasets.get("analysis"),
        documents=datasets.get("documents"),
        sectors=datasets.get("sectors"),
    )

    if not report.empty:
        print("\nseverity summary:")
        print(report["severity"].value_counts())

        print("\nrule summary:")
        print(report["rule_id"].value_counts())
    else:
        print("no validation issues found")
