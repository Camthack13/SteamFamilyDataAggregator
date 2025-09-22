from __future__ import annotations
import argparse
import csv
import io
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from steam.clients import (
    resolve_steam64,
    fetch_friends,
    check_library_access,
    fetch_library,
)
from steam.aggregate import aggregate
from steam.util import slugify, is_steam64, unique_by_steam64

APP_HOST = "127.0.0.1"
APP_PORT = 8765

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger("steamagg")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

# In-memory stash for current session (simple and local only)
SESSION_STATE = {
    "seed_input": None,
    "seed64": None,
    "seed_accessible": None,
    "friends": [],  # list of dicts: {steam64, name}
    "access_checked": {},  # steam64 -> bool/None
}


@app.get("/")
def index():
    return render_template("index.html")


def parse_uploaded_csv(file_storage) -> List[Tuple[str, str]]:
    """Return list of (vanity, steam64) from optional uploaded CSV."""
    out = []
    if not file_storage or file_storage.filename == '':
        return out
    try:
        data = file_storage.stream.read().decode('utf-8', errors='ignore')
        rdr = csv.DictReader(io.StringIO(data))
        for row in rdr:
            vanity = (row.get('vanity') or '').strip()
            steam64_id = (row.get('steam64_id') or '').strip()
            out.append((vanity, steam64_id))
    except Exception as e:
        logger.exception("Failed to parse uploaded CSV: %s", e)
        flash("Could not parse the uploaded CSV. Ensure headers: vanity,steam64_id.", "error")
    return out


@app.post("/load_friends")
def load_friends():
    seed_input = (request.form.get("seed") or '').strip()
    csv_file = request.files.get('csv')

    if not seed_input and (not csv_file or csv_file.filename == ''):
        flash("Enter a seed user (vanity or 64-bit ID) or upload a CSV.", "error")
        return redirect(url_for('index'))

    # Resolve seed
    seed64, seed_err = resolve_steam64(seed_input) if seed_input else (None, None)
    if seed_input and not seed64:
        flash(f"Could not resolve seed: {seed_err or 'unknown error'}", "error")

    # Ingest CSV entries and resolve any vanities
    csv_entries = parse_uploaded_csv(csv_file)
    resolved: List[Tuple[str, Optional[str]]] = []
    for vanity, s64 in csv_entries:
        if s64 and is_steam64(s64):
            resolved.append((vanity or s64, s64))
        elif vanity:
            r, _err = resolve_steam64(vanity)
            if r:
                resolved.append((vanity, r))
        # else: skip blanks

    # Build friend candidate set from the seed's friends page if we have a seed64
    friends = []
    if seed64:
        try:
            friends = fetch_friends(seed64)
        except Exception as e:
            logger.exception("Failed to fetch friends: %s", e)
            flash("Could not load friends for the seed (parsed errors were logged).", "warn")

    # Merge any CSV users as additional candidates (besides the seed)
    for label, s64 in resolved:
        if s64 and s64 != seed64:
            friends.append({"steam64": s64, "name": label})

    # Deduplicate by steam64
    friends = unique_by_steam64(friends)

    # Seed accessibility check (non-blocking)
    seed_access = None
    if seed64:
        try:
            seed_access = check_library_access(seed64)
        except Exception:
            seed_access = False

    # Stash state
    SESSION_STATE.update({
        "seed_input": seed_input,
        "seed64": seed64,
        "seed_accessible": seed_access,
        "friends": friends,
        "access_checked": {},
    })

    return render_template("friends.html", seed64=seed64, seed_access=seed_access, friends=friends)


@app.post("/check_access")
def check_access():
    steam64 = (request.form.get("steam64") or '').strip()
    if not steam64:
        return render_template("_badge.html", status="error", text="No ID"), 400
    try:
        ok = check_library_access(steam64)
    except Exception:
        ok = False
    SESSION_STATE["access_checked"][steam64] = ok
    return render_template("_badge.html", status=("ok" if ok else "bad"), text=("OK" if ok else "Not accessible"))


@app.post("/run")
def run_pass1():
    # Selected friend ids (checkboxes)
    selected = request.form.getlist('friend')  # list of steam64 strings
    selected = list(dict.fromkeys([s for s in selected if s]))  # dedupe preserve order

    included_users: List[str] = []
    excluded_users: List[str] = []

    seed64 = SESSION_STATE.get("seed64")
    seed_access = SESSION_STATE.get("seed_accessible")

    # Determine who to include
    if seed64 and seed_access:
        included_users.append(seed64)
    elif seed64 and not seed_access:
        flash("Seed library appears private/unavailable; proceeding with accessible friends only.", "warn")

    # For selected friends: include if accessible, else keep but mark excluded
    # Immediate validation may have run; if absent, re-check now.
    for s64 in selected:
        ok = SESSION_STATE["access_checked"].get(s64)
        if ok is None:
            try:
                ok = check_library_access(s64)
            except Exception:
                ok = False
        if ok:
            included_users.append(s64)
        else:
            excluded_users.append(s64)

    included_users = list(dict.fromkeys(included_users))

    if not included_users:
        flash("No accessible profiles selected (seed + friends). Please select at least one accessible profile.", "error")
        return redirect(url_for('index'))

    # Fetch libraries
    games_by_user: Dict[str, List[dict]] = {}
    errors: List[str] = []
    for uid in included_users:
        try:
            rows = fetch_library(uid)
            games_by_user[uid] = rows
        except Exception as e:
            logger.exception("Library fetch failed for %s: %s", uid, e)
            errors.append(uid)

    if not games_by_user:
        flash("Failed to fetch any libraries due to network/parse errors.", "error")
        return redirect(url_for('index'))

    # Aggregate
    agg_rows = aggregate(games_by_user)

    # Write CSV
    os.makedirs('output', exist_ok=True)
    seed_slug = slugify(SESSION_STATE.get("seed_input") or (seed64 or "unknown"))
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M')
    csv_path = os.path.join('output', f'libraries_{ts}_seed-{seed_slug}.csv')

    headers = ["appid", "name", "family_playtime_forever_h", "family_playtime_recent_h", "owners_count"]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in agg_rows:
            w.writerow(row)

    if excluded_users:
        flash(f"Run complete: {len(included_users)} included, {len(excluded_users)} excluded (private/inaccessible).", "info")

    return render_template("results.html", rows=agg_rows, csv_path=csv_path)


# ---------------------------
# Optional CLI (no UI)
# ---------------------------

def run_cli(seed: Optional[str], input_csv: Optional[str]):
    if not seed and not input_csv:
        print("Provide --seed or --input-csv for CLI mode.")
        return

    seed64 = None
    if seed:
        seed64, err = resolve_steam64(seed)
        if not seed64:
            print(f"Seed could not be resolved: {err}")

    candidates = []
    if seed64:
        try:
            candidates = fetch_friends(seed64)
        except Exception as e:
            logger.warning("CLI: could not fetch friends: %s", e)

    # ingest CSV
    if input_csv and os.path.exists(input_csv):
        with open(input_csv, 'r', encoding='utf-8') as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                vanity = (row.get('vanity') or '').strip()
                s64 = (row.get('steam64_id') or '').strip()
                if s64 and is_steam64(s64):
                    candidates.append({"steam64": s64, "name": vanity or s64})
                elif vanity:
                    r, _ = resolve_steam64(vanity)
                    if r:
                        candidates.append({"steam64": r, "name": vanity})

    candidates = unique_by_steam64(candidates)

    included = []
    if seed64 and check_library_access(seed64):
        included.append(seed64)

    # choose up to 5 first accessible friends
    for c in candidates:
        if len(included) >= (1 + 5):
            break
        s64 = c['steam64']
        if check_library_access(s64):
            included.append(s64)

    if not included:
        print("CLI: no accessible profiles.")
        return

    games_by_user = {}
    for uid in included:
        try:
            games_by_user[uid] = fetch_library(uid)
        except Exception as e:
            logger.warning("CLI: library fetch failed for %s: %s", uid, e)

    agg_rows = aggregate(games_by_user)

    os.makedirs('output', exist_ok=True)
    seed_slug = slugify(seed or (seed64 or "unknown"))
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M')
    csv_path = os.path.join('output', f'libraries_{ts}_seed-{seed_slug}.csv')
    headers = ["appid", "name", "family_playtime_forever_h", "family_playtime_recent_h", "owners_count"]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in agg_rows:
            w.writerow(row)
    print(f"Wrote {len(agg_rows)} rows to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steam Family Library Aggregator – Pass 1")
    parser.add_argument('--seed', help='Seed vanity or steam64 (CLI mode)')
    parser.add_argument('--input-csv', help='Optional CSV with vanity,steam64_id (CLI mode)')
    parser.add_argument('--no-ui', action='store_true', help='Run CLI mode (no web UI)')
    args = parser.parse_args()

    if args.no_ui:
        run_cli(args.seed, args.input_csv)
    else:
        app.run(host=APP_HOST, port=APP_PORT, debug=False)
