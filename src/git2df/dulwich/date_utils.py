import datetime
import parsedatetime as pdt
from typing import Optional

def parse_date_string(date_string: str) -> Optional[datetime.datetime]:
    cal = pdt.Calendar(version=pdt.VERSION_CONTEXT_STYLE)
    result, parse_status = cal.parseDT(
        date_string, sourceTime=datetime.datetime.now(datetime.timezone.utc)
    )

    if result:  # If result is not None, parsing was successful
        # parsedatetime returns naive datetime objects, so we need to make them timezone-aware
        # If the parsed datetime is naive, assume UTC
        if result.tzinfo is None:
            result = result.replace(tzinfo=datetime.timezone.utc)
        return result
    return None

def get_date_filters(
    since: Optional[str], until: Optional[str]
) -> tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    since_dt = None
    if since:
        since_dt = parse_date_string(since)
        if not since_dt:
            # logger.warning(f"Unsupported 'since' format: {since}. Ignoring.")
            pass
    else:
        # Default to last year if no 'since' is provided
        since_dt = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(days=365)

    until_dt = None
    if until:
        until_dt = parse_date_string(until)
        if not until_dt:
            # logger.warning(f"Unsupported 'until' format: {until}. Ignoring.")
            pass
    else:
        # Default to now if no 'until' is provided
        until_dt = datetime.datetime.now(datetime.timezone.utc)
    return since_dt, until_dt
