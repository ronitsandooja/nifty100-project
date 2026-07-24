from src.analytics.cagr import cagr, shift_year, compute_cagr_for_window


# cagr formula and edge cases

def test_cagr_normal_growth():
    value, flag = cagr(100, 200, 5)
    assert round(value, 2) == 14.87
    assert flag is None

def test_cagr_decline_to_loss():
    value, flag = cagr(100, -50, 3)
    assert value is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_decline_to_zero():
    value, flag = cagr(100, 0, 3)
    assert value is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_turnaround():
    value, flag = cagr(-100, 200, 3)
    assert value is None
    assert flag == "TURNAROUND"

def test_cagr_both_negative():
    value, flag = cagr(-100, -50, 3)
    assert value is None
    assert flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    value, flag = cagr(0, 100, 3)
    assert value is None
    assert flag == "ZERO_BASE"

def test_cagr_insufficient_years():
    value, flag = cagr(100, 200, 0)
    assert value is None
    assert flag == "INSUFFICIENT"


# year lookup helpers

def test_shift_year_basic():
    assert shift_year("2023-03", 5) == "2018-03"

def test_shift_year_keeps_fiscal_month():
    assert shift_year("2024-09", 3) == "2021-09"

def test_compute_cagr_for_window_missing_start_year():
    rows_by_year = {"2023-03": {"sales": 1000}}
    value, flag = compute_cagr_for_window(rows_by_year, "2023-03", 5, "sales")
    assert value is None
    assert flag == "INSUFFICIENT"

def test_compute_cagr_for_window_normal():
    rows_by_year = {
        "2018-03": {"sales": 100},
        "2023-03": {"sales": 200},
    }
    value, flag = compute_cagr_for_window(rows_by_year, "2023-03", 5, "sales")
    assert round(value, 2) == 14.87
    assert flag is None
