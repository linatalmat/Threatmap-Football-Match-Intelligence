"""telecharger les donnee StatBomb open data (ligue 1 2025/2016) dans data/raw"""
import json 
import logging 
import time 
from pathlib import Path 

import requests 
from requests.adapters import HTTPAdapter 
from urllib3.util.retry import Retry 

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
COMPETITION_ID = 7
SEASON_ID = 27
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest")

def make_session() -> requests.Session:
    
    retry = Retry(
        total=5,
        backoff_factor=1,  
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

def download_json(session: requests.Session, url: str, dest: Path) -> bool:
    """Télécharge url vers dest. Retourne True si téléchargé, False si déjà présent."""
    if dest.exists() and dest.stat().st_size > 0:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = session.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()  
    tmp = dest.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(dest) 
    return True

def main() -> None:
    session = make_session()

    matches_path = RAW_DIR / f"matches_{COMPETITION_ID}_{SEASON_ID}.json"
    download_json(
        session, f"{BASE_URL}/matches/{COMPETITION_ID}/{SEASON_ID}.json", matches_path
    )
    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    log.info("%d matchs dans la liste", len(matches))

    downloaded, skipped, failed = 0, 0, []
    for i, match in enumerate(matches, start=1):
        match_id = match["match_id"]
        try:
            for kind in ("events", "lineups"):
                dest = RAW_DIR / kind / f"{match_id}.json"
                if download_json(session, f"{BASE_URL}/{kind}/{match_id}.json", dest):
                    downloaded += 1
                    time.sleep(0.2)  # politesse envers GitHub
                else:
                    skipped += 1
        except (requests.RequestException, ValueError) as exc:
            log.error("match %s : échec (%s)", match_id, exc)
            failed.append(match_id)
        if i % 25 == 0:
            log.info("progression : %d/%d matchs", i, len(matches))

    log.info("terminé : %d téléchargés, %d déjà présents, %d échecs",
             downloaded, skipped, len(failed))
    if failed:
        log.warning("matchs en échec (relance le script) : %s", failed)


if __name__ == "__main__":
    main()