import pandas as pd

from src.etl.validator import (
    validation_results,
    dq01_company_pk,
    dq03_fk,
    dq05_opm,
    dq06_sales,
    dq16_coverage,
)


def reset():
    validation_results.clear()


# pk check

def test_duplicate_company_id():
    reset()

    df = pd.DataFrame({"id": ["TCS", "TCS"]})

    dq01_company_pk(df)

    assert len(validation_results) == 2
    assert validation_results[0]["rule_id"] == "DQ-01"


# fk check

def test_invalid_foreign_key():
    reset()

    companies = pd.DataFrame({"id": ["TCS"]})
    pnl = pd.DataFrame({
        "company_id": ["ABC"],
        "year": ["2024-03"]
    })

    dq03_fk(pnl, companies, "pnl")

    assert len(validation_results) == 1
    assert validation_results[0]["rule_id"] == "DQ-03"


# opm checks

def test_opm_mismatch():
    reset()

    pnl = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"],
        "sales": [1000],
        "operating_profit": [200],
        "opm_percentage": [10]
    })

    dq05_opm(pnl)

    assert len(validation_results) == 1
    assert validation_results[0]["rule_id"] == "DQ-05"


def test_opm_valid():
    reset()

    pnl = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"],
        "sales": [1000],
        "operating_profit": [200],
        "opm_percentage": [20]
    })

    dq05_opm(pnl)

    assert len(validation_results) == 0


# sales checks

def test_negative_sales():
    reset()

    pnl = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"],
        "sales": [-10]
    })

    dq06_sales(pnl)

    assert len(validation_results) == 1
    assert validation_results[0]["rule_id"] == "DQ-06"


def test_positive_sales():
    reset()

    pnl = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"],
        "sales": [100]
    })

    dq06_sales(pnl)

    assert len(validation_results) == 0


# coverage checks

def test_coverage_failure():
    reset()

    companies = pd.DataFrame({"id": ["TCS"]})

    pnl = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"]
    })

    bs = pnl.copy()
    cf = pnl.copy()

    dq16_coverage(companies, pnl, bs, cf)

    assert len(validation_results) > 0
    assert validation_results[0]["rule_id"] == "DQ-16"


def test_coverage_valid():
    reset()

    companies = pd.DataFrame({"id": ["TCS"]})

    data = pd.DataFrame({
        "company_id": ["TCS"] * 5,
        "year": [
            "2020-03",
            "2021-03",
            "2022-03",
            "2023-03",
            "2024-03"
        ]
    })

    dq16_coverage(companies, data, data, data)

    assert len(validation_results) == 0
