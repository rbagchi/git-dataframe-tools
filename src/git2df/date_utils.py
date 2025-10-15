import parsedatetime as pdt
from datetime import datetime, timezone

def get_date_filters(since, until):
    cal = pdt.Calendar(version=pdt.VERSION_CONTEXT_STYLE)
    now = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    now_start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    now_end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    since_dt, since_parse_result = cal.parseDT(since, now_start_of_day) if since else (None, None)
    until_dt, until_parse_result = cal.parseDT(until, now_end_of_day) if until else (None, None)

    if since_dt and since_dt.tzinfo is None:
        since_dt = since_dt.replace(tzinfo=timezone.utc)

    if until_dt and until_dt.tzinfo is None:
        until_dt = until_dt.replace(tzinfo=timezone.utc)

    # If 'until' was a date only (no time specified), ensure it's set to the end of the day
    if until_dt and until_parse_result.accuracy == pdt.pdtContext.ACU_DATE:
        until_dt = until_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    # If 'since' was a date only (no time specified), ensure it's set to the beginning of the day
    if since_dt and since_parse_result.accuracy == pdt.pdtContext.ACU_DATE:
        since_dt = since_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    return since_dt, until_dt
