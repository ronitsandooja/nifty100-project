from src.etl.normaliser import (
    normalize_ticker,
    clean_text,
    to_float,
    normalize_year
)


# ticker tests

def test_ticker_basic():
    assert normalize_ticker("tcs") == "TCS"

def test_ticker_spaces():
    assert normalize_ticker("  infy  ") == "INFY"

def test_ticker_mixed_case():
    assert normalize_ticker("ReLiAnCe") == "RELIANCE"

def test_ticker_empty():
    assert normalize_ticker("") is None

def test_ticker_none():
    assert normalize_ticker(None) is None

def test_ticker_numeric():
    assert normalize_ticker(123) == "123"

def test_ticker_special():
    assert normalize_ticker(" tcs@ ") == "TCS@"

def test_ticker_whitespace_only():
    assert normalize_ticker("   ") is None

def test_ticker_special_inside():
    assert normalize_ticker("ab@c") == "AB@C"


# text cleaning tests

def test_clean_text_basic():
    assert clean_text(" hello ") == "hello"

def test_clean_text_newline():
    assert clean_text("hello\nworld") == "hello world"

def test_clean_text_empty():
    assert clean_text("") is None

def test_clean_text_none():
    assert clean_text(None) is None

def test_clean_text_multiple_spaces():
    assert clean_text("  hello   world  ") == "hello   world"

def test_clean_text_only_newline():
    assert clean_text("\n") is None

def test_clean_text_tabs():
    assert clean_text("\t hello \t") == "hello"

def test_clean_text_mixed_whitespace():
    assert clean_text(" \n hello \t ") == "hello"


# numeric conversion tests

def test_float_integer():
    assert to_float(100) == 100.0

def test_float_decimal():
    assert to_float(125.50) == 125.50

def test_float_comma():
    assert to_float("1,250") == 1250.0

def test_float_percentage():
    assert to_float("15%") == 15.0

def test_float_blank():
    assert to_float("") is None

def test_float_invalid():
    assert to_float("abc") is None

def test_float_negative():
    assert to_float("-100") == -100.0

def test_float_spaces():
    assert to_float(" 200 ") == 200.0

def test_float_comma_percent():
    assert to_float("1,200%") == 1200.0

def test_float_zero():
    assert to_float("0") == 0.0

def test_float_large_number():
    assert to_float("10,00,000") == 1000000.0


# year normalization tests

def test_year_mar_format():
    assert normalize_year("Mar-24") == "2024-03"

def test_year_dec_format():
    assert normalize_year("Dec-24") == "2024-12"

def test_year_space_format():
    assert normalize_year("Mar 24") == "2024-03"

def test_year_full_month():
    assert normalize_year("December 2024") == "2024-12"

def test_year_lowercase_month():
    assert normalize_year("mar-24") == "2024-03"

def test_year_mixed_format():
    assert normalize_year("Mar-2024") == "2024-03"

def test_year_fy24():
    assert normalize_year("FY24") == "2024-03"

def test_year_fy23():
    assert normalize_year("FY23") == "2023-03"

def test_year_plain():
    assert normalize_year("2024") == "2024-03"

def test_year_already_formatted():
    assert normalize_year("2024-03") == "2024-03"

def test_year_invalid():
    assert normalize_year("something") is None

def test_year_empty():
    assert normalize_year("") is None

def test_year_none():
    assert normalize_year(None) is None
