from __future__ import annotations
from lxml import etree, html
from typing import List, Tuple
import re

HOURS_RE = re.compile(r"([0-9]+(?:[\.,][0-9]+)?)")


def parse_steam64_from_vanity_xml(xml_bytes: bytes) -> Tuple[str|None, str|None]:
    try:
        root = etree.fromstring(xml_bytes)
        el = root.find('.//steamID64')
        if el is not None and el.text and el.text.strip():
            return el.text.strip(), None
        return None, "steamID64 not found"
    except Exception as e:
        return None, f"XML parse error: {e}"


def parse_friends(html_bytes: bytes) -> List[dict]:
    doc = html.fromstring(html_bytes)
    out = []
    # data-steamid attributes are reliable
    for el in doc.cssselect('[data-steamid]'):
        s64 = el.get('data-steamid')
        # Try to find a visible name nearby
        name = el.text_content().strip() or s64
        out.append({"steam64": s64, "name": name})
    # Fallback: anchors with steam profiles
    if not out:
        for a in doc.xpath('//a[contains(@href, "/profiles/") or contains(@href, "/id/")]'):
            s64 = a.get('data-steamid') or ''
            if not s64:
                # try to pull from href when it's /profiles/<id>
                href = a.get('href') or ''
                m = re.search(r"/profiles/([0-9]{17})", href)
                if m:
                    s64 = m.group(1)
            if s64:
                name = a.text_content().strip() or s64
                out.append({"steam64": s64, "name": name})
    return out


def parse_hours(text: str|None) -> float:
    if not text:
        return 0.0
    # remove common phrases
    t = text.lower()
    # pick the first numeric like 123, 12.5, 12,5
    m = HOURS_RE.search(t)
    if not m:
        return 0.0
    num = m.group(1).replace(',', '.')
    try:
        return float(num)
    except ValueError:
        return 0.0


def parse_library_xml(xml_bytes: bytes) -> List[dict]:
    out = []
    root = etree.fromstring(xml_bytes)
    # gamesList/games/game
    for g in root.findall('.//gamesList/games/game'):
        appid = (g.findtext('appID') or '').strip()
        name = (g.findtext('name') or '').strip()
        hours_all = parse_hours(g.findtext('hoursOnRecord'))
        hours_recent = parse_hours(g.findtext('hoursLast2Weeks'))
        if appid:
            out.append({
                "appid": appid,
                "name": name,
                "hoursOnRecord": hours_all,
                "hoursLast2Weeks": hours_recent,
            })
    return out