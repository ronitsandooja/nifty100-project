import sqlite3
import pandas as pd

from src.etl.loader import load_all_datasets
from src.analytics.ratios import (
    net_profit_margin, operating_profit_margin, return_on_equity,
    return_on_capital_employed, return_on_assets, debt_to_equity,
    is_high_leverage, interest_coverage, icr_warning, asset_turnover
)
from src.analytics.cagr import compute_cagr_for_window, shift_year
from src.analytics.cashflow_kpis import (
    free_cash_flow, capex_intensity, fcf_conversion_rate,
    cfo_quality_score, capital_allocation_pattern
)

edge_cases = []


def log_edge_case(company_id, year, category, message):
    edge_cases.append({
        "company_id": company_id,
        "year": year,
        "category": category,
        "message": message
    })


def group_by_year(df):
    lookup = {}
    for company_id, group in df.groupby("company_id"):
        rows = {}
        for _, row in group.iterrows():
            rows[row["year"]] = row
        lookup[company_id] = rows
    return lookup


def book_value_per_share(equity_capital, reserves, face_value):
    if face_value is None or face_value == 0:
        return None
    shares = equity_capital / face_value
    if shares <= 0:
        return None
    return (equity_capital + reserves) / shares


def scale_to_100(value, low, high):
    if value is None or pd.isna(value) or low is None or high is None or high == low:
        return None
    scaled = (value - low) / (high - low) * 100
    return max(0, min(100, scaled))


def compute_one_row(company_id, year, pnl_row, bs_row, cf_row, is_financial, face_value):
    row = {"company_id": company_id, "year": year}

    row["net_profit_margin_pct"] = net_profit_margin(pnl_row["net_profit"], pnl_row["sales"])
    row["operating_profit_margin_pct"] = operating_profit_margin(pnl_row["operating_profit"], pnl_row["sales"])
    row["earnings_per_share"] = pnl_row["eps"]
    row["dividend_payout_ratio_pct"] = pnl_row["dividend_payout"]

    if row["operating_profit_margin_pct"] is not None:
        diff = abs(row["operating_profit_margin_pct"] - pnl_row["opm_percentage"])
        if diff > 1:
            log_edge_case(company_id, year, "opm_mismatch",
                          f"computed opm={round(row['operating_profit_margin_pct'], 2)} vs source opm={pnl_row['opm_percentage']}")

    if bs_row is not None:
        row["return_on_equity_pct"] = return_on_equity(pnl_row["net_profit"], bs_row["equity_capital"], bs_row["reserves"])
        roce = return_on_capital_employed(
            pnl_row["operating_profit"], pnl_row["depreciation"],
            bs_row["equity_capital"], bs_row["reserves"], bs_row["borrowings"]
        )
        de = debt_to_equity(bs_row["borrowings"], bs_row["equity_capital"], bs_row["reserves"])

        row["debt_to_equity"] = de
        row["asset_turnover"] = asset_turnover(pnl_row["sales"], bs_row["total_assets"])
        row["total_debt_cr"] = bs_row["borrowings"]
        row["book_value_per_share"] = book_value_per_share(bs_row["equity_capital"], bs_row["reserves"], face_value)
        row["_roce"] = roce

        if is_high_leverage(de, is_financial):
            log_edge_case(company_id, year, "leverage", f"D/E={round(de, 2)} > 5, flagged high leverage")
    else:
        row["return_on_equity_pct"] = None
        row["debt_to_equity"] = None
        row["asset_turnover"] = None
        row["total_debt_cr"] = None
        row["book_value_per_share"] = None
        row["_roce"] = None

    icr = interest_coverage(pnl_row["operating_profit"], pnl_row["other_income"], pnl_row["interest"])
    row["interest_coverage"] = icr

    if icr is None:
        log_edge_case(company_id, year, "debt_free_substitution", "interest = 0, ICR set to None (Debt Free)")
    elif icr_warning(icr):
        log_edge_case(company_id, year, "interest_risk", f"ICR={round(icr, 2)} < 1.5")

    if cf_row is not None:
        fcf = free_cash_flow(cf_row["operating_activity"], cf_row["investing_activity"])
        row["free_cash_flow_cr"] = fcf
        row["capex_cr"] = abs(cf_row["investing_activity"])
        row["cash_from_operations_cr"] = cf_row["operating_activity"]
        row["_fcf_conversion"] = fcf_conversion_rate(fcf, pnl_row["operating_profit"])
    else:
        row["free_cash_flow_cr"] = None
        row["capex_cr"] = None
        row["cash_from_operations_cr"] = None
        row["_fcf_conversion"] = None

    return row


def build_capital_allocation(pnl, cf_lookup):
    rows = []
    for _, pnl_row in pnl.iterrows():
        company_id = pnl_row["company_id"]
        cf_row = cf_lookup.get(company_id, {}).get(pnl_row["year"])

        if cf_row is None:
            continue

        cfo_sign, cfi_sign, cff_sign, label = capital_allocation_pattern(
            cf_row["operating_activity"], cf_row["investing_activity"],
            cf_row["financing_activity"], pnl_row["net_profit"]
        )
        rows.append({
            "company_id": company_id,
            "year": pnl_row["year"],
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern_label": label
        })

    return pd.DataFrame(rows)


def check_implausible_ratios(df):
    extreme = df[(df["return_on_equity_pct"] > 200) | (df["return_on_equity_pct"] < -200)]
    for _, row in extreme.iterrows():
        log_edge_case(row["company_id"], row["year"], "implausible_roe",
                      f"return_on_equity_pct={round(row['return_on_equity_pct'], 1)} is outside a plausible range, "
                      f"likely a very small equity_capital + reserves base in the source data (data source issue)")

    extreme_roce = df[(df["_roce"] > 200) | (df["_roce"] < -200)]
    for _, row in extreme_roce.iterrows():
        log_edge_case(row["company_id"], row["year"], "implausible_roce",
                      f"roce={round(row['_roce'], 1)} is outside a plausible range (data source issue)")


def check_source_anomalies(companies, ratios_df):
    latest = ratios_df.sort_values("year").groupby("company_id").tail(1)

    for _, row in latest.iterrows():
        company_id = row["company_id"]
        source = companies[companies["id"] == company_id]
        if source.empty:
            continue

        source_roce = source["roce_percentage"].iloc[0]
        source_roe = source["roe_percentage"].iloc[0]

        if pd.notna(source_roce) and pd.notna(row["_roce"]):
            diff = abs(row["_roce"] - source_roce)
            if diff > 5:
                category = "data source issue" if source_roce < 5 else "formula discrepancy"
                log_edge_case(company_id, row["year"], "roce_source_mismatch",
                              f"computed={round(row['_roce'], 2)} vs source={source_roce} ({category})")

        if pd.notna(source_roe) and pd.notna(row["return_on_equity_pct"]):
            diff = abs(row["return_on_equity_pct"] - source_roe)
            if diff > 5:
                category = "data source issue" if source_roe < 5 else "formula discrepancy"
                log_edge_case(company_id, row["year"], "roe_source_mismatch",
                              f"computed={round(row['return_on_equity_pct'], 2)} vs source={source_roe} ({category})")


def add_cagr_columns(df, pnl_lookup):
    for window in (3, 5, 10):
        rev_col = []
        pat_col = []
        eps_col = []

        for _, row in df.iterrows():
            company_id = row["company_id"]
            rows_by_year = pnl_lookup[company_id]

            rev_cagr, rev_flag = compute_cagr_for_window(rows_by_year, row["year"], window, "sales")
            pat_cagr, pat_flag = compute_cagr_for_window(rows_by_year, row["year"], window, "net_profit")
            eps_cagr, eps_flag = compute_cagr_for_window(rows_by_year, row["year"], window, "eps")

            rev_col.append(rev_cagr)
            pat_col.append(pat_cagr)
            eps_col.append(eps_cagr)

            if rev_flag and rev_flag != "INSUFFICIENT":
                log_edge_case(company_id, row["year"], "cagr_flag", f"revenue_cagr_{window}yr = {rev_flag}")
            if pat_flag and pat_flag != "INSUFFICIENT":
                log_edge_case(company_id, row["year"], "cagr_flag", f"pat_cagr_{window}yr = {pat_flag}")

        df[f"revenue_cagr_{window}yr"] = rev_col
        df[f"pat_cagr_{window}yr"] = pat_col
        df[f"eps_cagr_{window}yr"] = eps_col

    return df


def add_cfo_quality(df, pnl_lookup, cf_lookup):
    scores = []
    for _, row in df.iterrows():
        company_id = row["company_id"]
        p_rows = pnl_lookup.get(company_id, {})
        c_rows = cf_lookup.get(company_id, {})

        pairs = []
        for offset in range(5):
            y = shift_year(row["year"], offset)
            if y in p_rows and y in c_rows:
                pairs.append((c_rows[y]["operating_activity"], p_rows[y]["net_profit"]))

        score, label = cfo_quality_score(pairs)
        scores.append(score)

    df["cfo_quality_score"] = scores
    return df


def add_composite_score(df):
    de_inverted = df["debt_to_equity"].apply(lambda x: -x if pd.notna(x) else None)

    roe_low, roe_high = df["return_on_equity_pct"].quantile([0.1, 0.9])
    fcf_low, fcf_high = df["_fcf_conversion"].quantile([0.1, 0.9])
    roce_low, roce_high = df["_roce"].quantile([0.1, 0.9])
    de_low, de_high = de_inverted.quantile([0.1, 0.9])

    scores = []
    for _, row in df.iterrows():
        roe_score = scale_to_100(row["return_on_equity_pct"], roe_low, roe_high)
        fcf_score = scale_to_100(row["_fcf_conversion"], fcf_low, fcf_high)
        roce_score = scale_to_100(row["_roce"], roce_low, roce_high)
        de_score = scale_to_100(-row["debt_to_equity"] if pd.notna(row["debt_to_equity"]) else None, de_low, de_high)

        parts = [(roe_score, 0.30), (fcf_score, 0.25), (roce_score, 0.25), (de_score, 0.20)]
        available = [(s, w) for s, w in parts if s is not None]

        if not available:
            scores.append(None)
            continue

        total_weight = sum(w for _, w in available)
        composite = sum(s * w for s, w in available) / total_weight
        scores.append(round(composite, 1))

    df["composite_quality_score"] = scores
    return df


def build_financial_ratios():
    edge_cases.clear()

    datasets = load_all_datasets()

    companies = datasets["companies"]
    pnl = datasets["profitandloss"]
    bs = datasets["balancesheet"]
    cf = datasets["cashflow"]
    sectors = datasets["sectors"]

    financial_ids = set(sectors[sectors["broad_sector"] == "Financials"]["company_id"])
    face_values = companies.set_index("id")["face_value"]

    bs_lookup = group_by_year(bs)
    cf_lookup = group_by_year(cf)
    pnl_lookup = group_by_year(pnl)

    rows = []
    for _, pnl_row in pnl.iterrows():
        company_id = pnl_row["company_id"]

        bs_row = bs_lookup.get(company_id, {}).get(pnl_row["year"])
        cf_row = cf_lookup.get(company_id, {}).get(pnl_row["year"])
        is_financial = company_id in financial_ids
        face_value = face_values.get(company_id)

        row = compute_one_row(company_id, pnl_row["year"], pnl_row, bs_row, cf_row, is_financial, face_value)
        rows.append(row)

    df = pd.DataFrame(rows)

    df = add_cagr_columns(df, pnl_lookup)
    df = add_cfo_quality(df, pnl_lookup, cf_lookup)
    df = add_composite_score(df)

    check_implausible_ratios(df)
    check_source_anomalies(companies, df)

    capital_allocation_df = build_capital_allocation(pnl, cf_lookup)

    final_columns = [
        "company_id", "year",
        "net_profit_margin_pct", "operating_profit_margin_pct", "return_on_equity_pct",
        "debt_to_equity", "interest_coverage", "asset_turnover",
        "free_cash_flow_cr", "capex_cr", "earnings_per_share", "book_value_per_share",
        "dividend_payout_ratio_pct", "total_debt_cr", "cash_from_operations_cr",
        "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr", "composite_quality_score"
    ]

    return df[final_columns], capital_allocation_df


def save_financial_ratios(df, db_path="db/nifty100.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("delete from financial_ratios")
    df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def save_capital_allocation(df):
    df.to_csv("output/capital_allocation.csv", index=False)


def save_edge_case_log():
    with open("output/ratio_edge_cases.log", "w") as f:
        for case in edge_cases:
            f.write(f"{case['company_id']} | {case['year']} | {case['category']} | {case['message']}\n")


if __name__ == "__main__":
    ratios_df, capital_allocation_df = build_financial_ratios()

    save_financial_ratios(ratios_df)
    save_capital_allocation(capital_allocation_df)
    save_edge_case_log()

    print(f"financial_ratios -> {len(ratios_df)} rows")
    print(f"capital_allocation.csv -> {len(capital_allocation_df)} rows")
    print(f"ratio_edge_cases.log -> {len(edge_cases)} entries")
