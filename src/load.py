"""Charge data/raw dans PostgreSQL. Relançable : ON CONFLICT DO NOTHING."""
import json
import logging
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, execute_values

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("load")

# Clés communes à tous les événements : le reste va dans `details`
COMMON_KEYS = {
    "id", "index", "period", "timestamp", "minute", "second", "type",
    "possession", "possession_team", "play_pattern", "team", "player",
    "position", "location", "duration", "under_pressure", "related_events",
    "off_camera", "out", "counterpress",
}


def connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def load_reference(cur, matches):
    """Remplit competitions, teams et matches."""
    comps, teams = {}, {}
    for m in matches:
        c, s = m["competition"], m["season"]
        comps[(c["competition_id"], s["season_id"])] = (
            c["competition_id"], s["season_id"],
            c["competition_name"], s["season_name"], c.get("country_name"),
        )
        for side in ("home", "away"):
            t = m[f"{side}_team"]
            teams[t[f"{side}_team_id"]] = (t[f"{side}_team_id"], t[f"{side}_team_name"])

    execute_values(cur, "INSERT INTO competitions VALUES %s ON CONFLICT DO NOTHING",
                   list(comps.values()))
    execute_values(cur, "INSERT INTO teams VALUES %s ON CONFLICT DO NOTHING",
                   list(teams.values()))
    rows = [(
        m["match_id"], m["competition"]["competition_id"], m["season"]["season_id"],
        m["match_date"], m.get("kick_off"), m.get("match_week"),
        m["home_team"]["home_team_id"], m["away_team"]["away_team_id"],
        m["home_score"], m["away_score"],
        (m.get("stadium") or {}).get("name"), (m.get("referee") or {}).get("name"),
    ) for m in matches]
    execute_values(cur, "INSERT INTO matches VALUES %s ON CONFLICT DO NOTHING", rows)


def load_players(cur, match_ids):
    """Remplit players depuis les fichiers lineups."""
    players = {}
    for mid in match_ids:
        for team in json.loads((RAW / "lineups" / f"{mid}.json").read_text("utf-8")):
            for p in team["lineup"]:
                players[p["player_id"]] = (
                    p["player_id"], p["player_name"], p.get("player_nickname"),
                    (p.get("country") or {}).get("name"),
                )
    execute_values(cur, "INSERT INTO players VALUES %s ON CONFLICT DO NOTHING",
                   list(players.values()))
    return set(players)


def load_events(cur, match_id, known_players):
    """Remplit events et shots pour un match."""
    events = json.loads((RAW / "events" / f"{match_id}.json").read_text("utf-8"))
    ev_rows, shot_rows = [], []
    for e in events:
        loc = e.get("location") or [None, None]
        pid = (e.get("player") or {}).get("id")
        if pid not in known_players:
            pid = None
        team_id = (e.get("team") or {}).get("id")
        details = {k: v for k, v in e.items() if k not in COMMON_KEYS}
        ev_rows.append((
            e["id"], match_id, e["index"], e.get("period"), e.get("minute"),
            e.get("second"), e["type"]["name"], team_id, pid, e.get("possession"),
            (e.get("possession_team") or {}).get("id"),
            (e.get("play_pattern") or {}).get("name"),
            loc[0], loc[1], bool(e.get("under_pressure")),
            Json(details) if details else None,
        ))
        if e["type"]["name"] == "Shot":
            s = e["shot"]
            end = s.get("end_location") or []
            end = end + [None] * (3 - len(end))  # 2 ou 3 valeurs selon le tir
            shot_rows.append((
                e["id"], match_id, team_id, pid, e.get("minute"), loc[0], loc[1],
                end[0], end[1], end[2],
                (s.get("body_part") or {}).get("name"),
                (s.get("type") or {}).get("name"),
                (s.get("technique") or {}).get("name"),
                (s.get("outcome") or {}).get("name"),
                bool(s.get("first_time")), s.get("statsbomb_xg"),
            ))
    execute_values(cur, "INSERT INTO events VALUES %s ON CONFLICT DO NOTHING", ev_rows)
    if shot_rows:
        execute_values(cur, "INSERT INTO shots VALUES %s ON CONFLICT DO NOTHING", shot_rows)
    return len(ev_rows), len(shot_rows)


def main():
    matches = json.loads((RAW / "matches_7_27.json").read_text("utf-8"))
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute((ROOT / "sql" / "01_schema.sql").read_text("utf-8"))
            load_reference(cur, matches)
            known = load_players(cur, [m["match_id"] for m in matches])
            conn.commit()
            log.info("référentiels chargés (%d joueurs)", len(known))

            total_ev = total_sh = 0
            for i, m in enumerate(matches, start=1):
                n_ev, n_sh = load_events(cur, m["match_id"], known)
                conn.commit()  # un commit par match
                total_ev += n_ev
                total_sh += n_sh
                if i % 25 == 0:
                    log.info("%d/%d matchs (%d événements, %d tirs)",
                             i, len(matches), total_ev, total_sh)
        log.info("terminé : %d événements, %d tirs", total_ev, total_sh)
    finally:
        conn.close()


if __name__ == "__main__":
    main()