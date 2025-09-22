from __future__ import annotations
import concurrent.futures as cf
import logging
from typing import List, Tuple, Dict

import requests
from lxml import html

from .parsers import (
    parse_steam64_from_vanity_xml,
    parse_friends,
    parse_library_xml,
)
from .rate_limit import HostGate, backoff_request
from .util import is_steam64

logger = logging.getLogger("steamagg.clients")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
SESSION.timeout = (15, 15)  # connect, read

GATE = HostGate(base_delay=0.8)

MAX_WORKERS = 3
BASE = "https://steamcommunity.com"


def _get(url: str) -> requests.Response:
    GATE.wait()
    def do():
        return SESSION.get(url, timeout=(15, 15))
    resp = backoff_request(do)
    return resp


def resolve_steam64(seed_str: str) -> Tuple[str|None, str|None]:
    seed_str = (seed_str or '').strip()
    if not seed_str:
        return None, "empty seed"
    if is_steam64(seed_str):
        return seed_str, None
    # vanity xml
    url = f"{BASE}/id/{seed_str}?xml=1"
    resp = _get(url)
    if resp.status_code != 200:
        return None, f"status {resp.status_code}"
    steam64, err = parse_steam64_from_vanity_xml(resp.content)
    return steam64, err


def fetch_friends(steam64: str) -> List[Dict]:
    results: List[Dict] = []
    # Try AJAX paginated endpoint if available
    page = 1
    while True:
        url = f"{BASE}/profiles/{steam64}/friends?ajax=1&p={page}"
        resp = _get(url)
        if resp.status_code != 200:
            break
        doc = html.fromstring(resp.text)
        chunk = parse_friends(resp.content)
        if not chunk:
            # if ajax returns minimal markup, fall back to non-ajax first page once
            if page == 1:
                url2 = f"{BASE}/profiles/{steam64}/friends"
                resp2 = _get(url2)
                if resp2.status_code == 200:
                    chunk = parse_friends(resp2.content)
            if not chunk:
                break
        results.extend(chunk)
        # Heuristic: if fewer than ~20 entries, likely last page
        if len(chunk) < 20:
            break
        page += 1
        if page > 50:
            break
    # Deduplicate by steam64 while preserving first name
    seen = set()
    deduped = []
    for r in results:
        s64 = r.get('steam64')
        if not s64 or s64 in seen:
            continue
        seen.add(s64)
        deduped.append(r)
    return deduped


def check_library_access(user_id: str) -> bool:
    # we always use /profiles/<steam64> form since we resolve upfront
    url = f"{BASE}/profiles/{user_id}/games?tab=all&xml=1"
    resp = _get(url)
    if resp.status_code != 200:
        return False
    try:
        rows = parse_library_xml(resp.content)
        # If it parsed without exception, consider accessible (even if empty)
        _ = len(rows)
        return True
    except Exception:
        return False


def fetch_library(user_id: str) -> List[Dict]:
    url = f"{BASE}/profiles/{user_id}/games?tab=all&xml=1"
    resp = _get(url)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    return parse_library_xml(resp.content)