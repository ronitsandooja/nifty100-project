pragma foreign_keys = on;

create table companies (
    id text primary key,
    company_logo text,
    company_name text not null,
    chart_link text,
    about_company text,
    website text,
    nse_profile text,
    bse_profile text,
    face_value real,
    book_value real,
    roce_percentage real,
    roe_percentage real
);

create table profitandloss (
    id integer primary key,
    company_id text not null,
    year text not null,

    sales real,
    expenses real,
    operating_profit real,
    opm_percentage real,
    other_income real,
    interest real,
    depreciation real,
    profit_before_tax real,
    tax_percentage real,
    net_profit real,
    eps real,
    dividend_payout real,

    unique(company_id, year),

    foreign key(company_id)
        references companies(id)
);

create table balancesheet (
    id integer primary key,
    company_id text not null,
    year text not null,

    equity_capital real,
    reserves real,
    borrowings real,
    other_liabilities real,
    total_liabilities real,

    fixed_assets real,
    cwip real,
    investments real,
    other_asset real,
    total_assets real,

    unique(company_id, year),

    foreign key(company_id)
        references companies(id)
);

create table cashflow (
    id integer primary key,
    company_id text not null,
    year text not null,

    operating_activity real,
    investing_activity real,
    financing_activity real,
    net_cash_flow real,

    unique(company_id, year),

    foreign key(company_id)
        references companies(id)
);

create table analysis (
    id integer primary key,
    company_id text not null,

    compounded_sales_growth text,
    compounded_profit_growth text,
    stock_price_cagr text,
    roe text,

    foreign key(company_id)
        references companies(id)
);

create table documents (
    id integer primary key,
    company_id text not null,
    year text,

    annual_report text,

    foreign key(company_id)
        references companies(id)
);

create table prosandcons (
    id integer primary key,
    company_id text not null,

    pros text,
    cons text,

    foreign key(company_id)
        references companies(id)
);

create table sectors (
    id integer primary key,
    company_id text not null,

    broad_sector text,
    sub_sector text,
    index_weight_pct real,
    market_cap_category text,

    foreign key(company_id)
        references companies(id)
);

create table financial_ratios (
    id integer primary key,
    company_id text not null,
    year text not null,

    net_profit_margin_pct real,
    operating_profit_margin_pct real,
    return_on_equity_pct real,
    debt_to_equity real,
    high_leverage_flag integer,
    interest_coverage real,
    icr_label text,
    asset_turnover real,
    free_cash_flow_cr real,
    capex_cr real,
    earnings_per_share real,
    book_value_per_share real,
    dividend_payout_ratio_pct real,
    total_debt_cr real,
    cash_from_operations_cr real,
    revenue_cagr_5yr real,
    revenue_cagr_5yr_flag text,
    pat_cagr_5yr real,
    pat_cagr_5yr_flag text,
    eps_cagr_5yr real,
    eps_cagr_5yr_flag text,
    composite_quality_score real,

    unique(company_id, year),

    foreign key(company_id)
        references companies(id)
);

create table market_cap (
    id integer primary key,
    company_id text not null,
    year text not null,

    market_cap_crore real,
    enterprise_value_crore real,
    pe_ratio real,
    pb_ratio real,
    ev_ebitda real,
    dividend_yield_pct real,

    unique(company_id, year),

    foreign key(company_id)
        references companies(id)
);

create table peer_groups (
    id integer primary key,
    peer_group_name text not null,
    company_id text not null,
    is_benchmark integer,

    foreign key(company_id)
        references companies(id)
);

create table stock_prices (
    id integer primary key,
    company_id text not null,
    date text not null,

    open_price real,
    high_price real,
    low_price real,
    close_price real,
    volume real,
    adjusted_close real,

    unique(company_id, date),

    foreign key(company_id)
        references companies(id)
);

create index idx_pnl_company
on profitandloss(company_id);

create index idx_bs_company
on balancesheet(company_id);

create index idx_cf_company
on cashflow(company_id);

create index idx_price_company
on stock_prices(company_id);

create index idx_price_date
on stock_prices(date);