import parsedatetime as pdt
from datetime import datetime, timezone

def _parse_and_localize_date(date_str, default_datetime, cal):
    if not date_str:
        return None

    dt, parse_result = cal.parseDT(date_str, default_datetime)

    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Adjust time based on whether it's a date-only string
    if dt and not ('T' in date_str or ':' in date_str or '+' in date_str):
        if default_datetime.hour == 0 and default_datetime.minute == 0 and default_datetime.second == 0: # Start of day
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        else: # End of day
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt

def get_date_filters(since, until):
    cal = pdt.Calendar(version=pdt.VERSION_CONTEXT_STYLE)
    now = datetime.now(timezone.utc)

    now_start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    now_end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    since_dt = _parse_and_localize_date(since, now_start_of_day, cal)
    until_dt = _parse_and_localize_date(until, now_end_of_day, cal)

    return since_dt, until_dt
