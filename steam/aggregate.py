from __future__ import annotations
from typing import Dict, List


def aggregate(games_by_user: Dict[str, List[dict]]) -> List[dict]:
    bucket: Dict[str, dict] = {}
    owners: Dict[str, set] = {}

    for uid, rows in games_by_user.items():
        for g in rows:
            appid = g['appid']
            name = g.get('name') or ''
            all_h = float(g.get('hoursOnRecord') or 0.0)
            rec_h = float(g.get('hoursLast2Weeks') or 0.0)

            if appid not in bucket:
                bucket[appid] = {
                    'appid': appid,
                    'name': name,
                    'family_playtime_forever_h': 0.0,
                    'family_playtime_recent_h': 0.0,
                }
                owners[appid] = set()
            bucket[appid]['family_playtime_forever_h'] += all_h
            bucket[appid]['family_playtime_recent_h'] += rec_h
            owners[appid].add(uid)

    # finalize rounding and owners_count
    out = []
    for appid, row in bucket.items():
        row['family_playtime_forever_h'] = round(row['family_playtime_forever_h'], 1)
        row['family_playtime_recent_h'] = round(row['family_playtime_recent_h'], 1)
        row['owners_count'] = len(owners.get(appid, set()))
        out.append(row)

    # default sort: forever desc
    out.sort(key=lambda r: (-r['family_playtime_forever_h'], r['name'].lower()))
    return out