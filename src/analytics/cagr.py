def cagr(start, end, years):
    if years is None or years <= 0:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"

    if start > 0 and end > 0:
        value = ((end / start) ** (1 / years) - 1) * 100
        return value, None

    if start > 0 and end <= 0:
        return None, "DECLINE_TO_LOSS"

    if start < 0 and end > 0:
        return None, "TURNAROUND"

    return None, "BOTH_NEGATIVE"


def shift_year(year_str, n):
    year_part, month_part = year_str.split("-")
    return f"{int(year_part) - n}-{month_part}"


def find_start_row(rows_by_year, end_year_str, window):
    start_year_str = shift_year(end_year_str, window)
    return rows_by_year.get(start_year_str)


def compute_cagr_for_window(rows_by_year, end_year_str, window, field):
    start_row = find_start_row(rows_by_year, end_year_str, window)

    if start_row is None:
        return None, "INSUFFICIENT"

    end_row = rows_by_year[end_year_str]

    start_value = start_row[field]
    end_value = end_row[field]

    return cagr(start_value, end_value, window)
