def free_cash_flow(operating_activity, investing_activity):
    return operating_activity + investing_activity


def capex_intensity(investing_activity, sales):
    if sales == 0:
        return None
    return abs(investing_activity) / sales * 100


def capex_intensity_label(capex_pct):
    if capex_pct is None:
        return None
    if capex_pct < 3:
        return "Asset Light"
    if capex_pct <= 8:
        return "Moderate"
    return "Capital Intensive"


def fcf_conversion_rate(fcf, operating_profit):
    if operating_profit == 0:
        return None
    return fcf / operating_profit * 100


def cfo_quality_score(cfo_pat_pairs):
    ratios = [cfo / pat for cfo, pat in cfo_pat_pairs if pat != 0]

    if not ratios:
        return None, None

    avg_ratio = sum(ratios) / len(ratios)

    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_ratio, label


def sign(value):
    return "+" if value > 0 else "-"


def capital_allocation_pattern(cfo, cfi, cff, net_profit):
    cfo_sign = sign(cfo)
    cfi_sign = sign(cfi)
    cff_sign = sign(cff)

    pattern = (cfo_sign, cfi_sign, cff_sign)

    labels = {
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
    }

    if pattern == ("+", "-", "-"):
        if net_profit != 0 and cfo / net_profit > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    else:
        label = labels.get(pattern, "Unclassified")

    return cfo_sign, cfi_sign, cff_sign, label
