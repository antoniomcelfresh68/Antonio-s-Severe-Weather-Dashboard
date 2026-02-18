# utils/severe_thunderstorm_warning_counter.py

import requests
from datetime import datetime, timezone

IEM_COW_URL = "https://mesonet.agron.iastate.edu/api/1/cow.json"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/json",
}

def fetch_svr_warning_count_ytd(year: int) -> int:
    """
    Returns an unofficial national YTD count of Severe Thunderstorm Warnings
    using IEM Cow storm-based warning stats (events_total).
    """
    start = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    params = {
        "phenomena": "SV",     # Severe Thunderstorm Warnings :contentReference[oaicite:3]{index=3}
        "begints": start,      # UTC ISO8601 :contentReference[oaicite:4]{index=4}
        "endts": end,
    }

    r = requests.get(IEM_COW_URL, params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    data = r.json()

    # Cow schema: stats.events_total :contentReference[oaicite:5]{index=5}
    return int(data["stats"]["events_total"])
