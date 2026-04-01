import json
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent.parent / "generated" / "engagement_state.json"

DEFAULT_STATE: dict = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
}


def load() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {k: (v.copy() if isinstance(v, (list, dict)) else v)
                for k, v in DEFAULT_STATE.items()}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
