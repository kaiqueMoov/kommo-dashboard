from datetime import datetime

def parse_date_param(value: str | None) -> datetime | None:
    if not value:
        return None

    value = value.strip()

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        if len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d")
        raise


def apply_date_filters(query, start: str | None, end: str | None):
    start_dt = parse_date_param(start)
    end_dt = parse_date_param(end)

    if start_dt:
        query = query.filter(Lead.created_at_kommo >= start_dt)

    if end_dt:
        query = query.filter(Lead.created_at_kommo < end_dt)

    return query