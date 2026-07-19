from src.etl.loader import load_all_datasets, build_database

# load once here so every test below can use it without re-reading all 12 excel files again
datasets = load_all_datasets()


# orphan / bad year checks

def test_companies_count():
    assert len(datasets["companies"]) == 92

def test_no_orphan_company_ids():
    valid_ids = set(datasets["companies"]["id"])
    assert datasets["profitandloss"]["company_id"].isin(valid_ids).all()

def test_no_missing_years():
    assert datasets["profitandloss"]["year"].isna().sum() == 0


# database build check

def test_database_builds_with_no_fk_errors():
    fk_errors = build_database(datasets, db_path="db/test_nifty100.db")
    assert fk_errors == []

    import os
    os.remove("db/test_nifty100.db")
