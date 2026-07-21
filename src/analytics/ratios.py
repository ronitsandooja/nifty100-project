# profitability ratios

def net_profit_margin(net_profit, sales):
    if sales == 0:
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit, sales):
    if sales == 0:
        return None
    return operating_profit / sales * 100


def return_on_equity(net_profit, equity_capital, reserves):
    equity = equity_capital + reserves
    if equity <= 0:
        return None
    return net_profit / equity * 100


def ebit(operating_profit, depreciation):
    return operating_profit - depreciation


def return_on_capital_employed(operating_profit, depreciation, equity_capital, reserves, borrowings):
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None
    return ebit(operating_profit, depreciation) / capital_employed * 100


def return_on_assets(net_profit, total_assets):
    if total_assets == 0:
        return None
    return net_profit / total_assets * 100


# leverage ratios

def debt_to_equity(borrowings, equity_capital, reserves):
    if borrowings == 0:
        return 0

    equity = equity_capital + reserves
    if equity <= 0:
        return None

    return borrowings / equity


def is_high_leverage(de_ratio, is_financial_sector):
    if de_ratio is None or is_financial_sector:
        return False
    return de_ratio > 5


def interest_coverage(operating_profit, other_income, interest):
    if interest == 0:
        return None
    return (operating_profit + other_income) / interest


def icr_label(icr_value):
    return "Debt Free" if icr_value is None else None


def icr_warning(icr_value):
    if icr_value is None:
        return False
    return icr_value < 1.5


def net_debt(borrowings, investments):
    return borrowings - investments


# efficiency ratios

def asset_turnover(sales, total_assets):
    if total_assets == 0:
        return None
    return sales / total_assets
