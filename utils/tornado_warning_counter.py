# utils/tornado_warning_counter.py

from __future__ import annotations
import io
import pandas as pd
import requests
from datetime import datetime, timezone

IEM_WATCHWARN = "https://mesonet.agron.iastate.edu/cgi-bin/request/gis/watchwarn.py"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "text/csv",
}

def fetch_tor_warning_count_ytd(year: int | None = None, timeout: int = 45) -> int:
    """
    Returns national YTD count of Tornado Warning *events* (unique by WFO+ETN+year+phenomena+significance),
    using IEM's VTEC archive CSV bulk service.
    """
    if year is None:
        year = datetime.now(timezone.utc).year

    sts = f"{year}-01-01T00:00Z"
    ets = f"{year+1}-01-01T00:00Z"

    params = {
        "accept": "csv",
        "sts": sts,
        "ets": ets,
        "limitps": "yes",
        "phenomena": "TO",
        "significance": "W",
    }

    r = requests.get(IEM_WATCHWARN, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()

    # Parse CSV
    df = pd.read_csv(io.StringIO(r.text))

    # Try common column names used by this service; fall back gracefully
    cols = {c.lower(): c for c in df.columns}

    # These are typically present in IEM watchwarn exports
    wfo_col = cols.get("wfo") or cols.get("office") or cols.get("wfo_id")
    etn_col = cols.get("etn") or cols.get("eventid") or cols.get("event_id")
    phen_col = cols.get("phenomena") or cols.get("phen")
    sig_col = cols.get("significance") or cols.get("sig")
    year_col = cols.get("year")

    required = [wfo_col, etn_col]
    if any(c is None for c in required):
        raise ValueError(f"Unexpected CSV schema. Columns: {list(df.columns)}")

    # If the CSV doesn’t include year/phen/sig, that’s fine; we already filtered the request.
    key_cols = [wfo_col, etn_col]
    for c in (year_col, phen_col, sig_col):
        if c is not None:
            key_cols.append(c)

    return int(df.drop_duplicates(subset=key_cols).shape[0])
