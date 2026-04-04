# utils/tornado_warning_counter.py

from __future__ import annotations
import io
import pandas as pd
from datetime import datetime, timezone
from typing import Optional
from utils.resilience import request_text

IEM_WATCHWARN = "https://mesonet.agron.iastate.edu/cgi-bin/request/gis/watchwarn.py"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "text/csv",
}

def _count_events_from_csv(csv_text: str) -> int:
    if not csv_text.strip():
        return 0

    try:
        df = pd.read_csv(io.StringIO(csv_text))
    except pd.errors.EmptyDataError:
        return 0

    if df.empty:
        return 0

    cols = {c.lower(): c for c in df.columns}

    wfo_col = cols.get("wfo") or cols.get("office") or cols.get("wfo_id")
    etn_col = cols.get("etn") or cols.get("eventid") or cols.get("event_id")
    phen_col = cols.get("phenomena") or cols.get("phen")
    sig_col = cols.get("significance") or cols.get("sig")
    year_col = cols.get("year")

    required = [wfo_col, etn_col]
    if any(c is None for c in required):
        raise ValueError(f"Unexpected CSV schema. Columns: {list(df.columns)}")

    key_cols = [wfo_col, etn_col]
    for c in (year_col, phen_col, sig_col):
        if c is not None:
            key_cols.append(c)

    return int(df.drop_duplicates(subset=key_cols).shape[0])


def fetch_tor_warning_count_ytd(year: Optional[int] = None, timeout: int = 45) -> int:
    """
    Returns national YTD count of Tornado Warning *events* (unique by WFO+ETN+year+phenomena+significance),
    using IEM's VTEC archive CSV bulk service.
    """
    if year is None:
        year = datetime.now(timezone.utc).year

    now = datetime.now(timezone.utc)
    sts = f"{year}-01-01T00:00Z"
    if year >= now.year:
        ets = now.strftime("%Y-%m-%dT%H:%MZ")
    else:
        ets = f"{year+1}-01-01T00:00Z"

    params = {
        "accept": "csv",
        "sts": sts,
        "ets": ets,
        "limitps": "yes",
        "phenomena": "TO",
        "significance": "W",
    }

    csv_text, _status = request_text(
        url=IEM_WATCHWARN,
        params=params,
        headers=HEADERS,
        timeout=min(timeout, 10),
        endpoint="iem.watchwarn.tornado_ytd",
        source="Iowa State IEM watchwarn",
        cache_key=f"iem:watchwarn:{year}:{sts}:{ets}",
    )
    count = _count_events_from_csv(csv_text)

    # The service can occasionally return an empty current-year window even when
    # the broader yearly query has data. Retry once with the full-year end bound
    # before accepting zero as the real answer.
    if count == 0 and year >= now.year and now.timetuple().tm_yday > 7:
        fallback_params = dict(params)
        fallback_params["ets"] = f"{year+1}-01-01T00:00Z"
        fallback_csv_text, _fallback_status = request_text(
            url=IEM_WATCHWARN,
            params=fallback_params,
            headers=HEADERS,
            timeout=min(timeout, 10),
            endpoint="iem.watchwarn.tornado_ytd_fallback",
            source="Iowa State IEM watchwarn",
            cache_key=f"iem:watchwarn:fallback:{year}",
        )
        fallback_count = _count_events_from_csv(fallback_csv_text)
        if fallback_count > 0:
            return fallback_count

    return count
