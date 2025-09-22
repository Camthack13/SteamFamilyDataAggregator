import re
from typing import List, Dict

STEAM64_RE = re.compile(r"^[0-9]{17}$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def is_steam64(s: str) -> bool:
    return bool(STEAM64_RE.match(s or ''))


def slugify(s: str) -> str:
    s = (s or '').lower().strip()
    s = SLUG_RE.sub('-', s)
    s = s.strip('-')
    return s or 'seed'


def unique_by_steam64(rows: List[Dict]):
    seen = set()
    out = []
    for r in rows:
        s64 = r.get('steam64')
        if not s64 or s64 in seen:
            continue
        seen.add(s64)
        out.append(r)
    return out


def library_url(id_or_vanity: str) -> str:
    if is_steam64(id_or_vanity):
        return f"https://steamcommunity.com/profiles/{id_or_vanity}/games?tab=all&xml=1"
    else:
        return f"https://steamcommunity.com/id/{id_or_vanity}/games?tab=all&xml=1"


def friends_url(id_or_vanity: str) -> str:
    if is_steam64(id_or_vanity):
        return f"https://steamcommunity.com/profiles/{id_or_vanity}/friends"
    else:
        return f"https://steamcommunity.com/id/{id_or_vanity}/friends"