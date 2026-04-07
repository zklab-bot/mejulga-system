import copy
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent.parent / "generated" / "engagement_state.json"

DEFAULT_STATE: dict = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
    "errors": [],
    "post_details": {},
}


def load() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return copy.deepcopy(DEFAULT_STATE)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def log_error(context: str, message: str) -> None:
    """Appends error to state errors list (keeps last 20)."""
    state = load()
    errors = state.setdefault("errors", [])
    errors.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": context,
        "message": message,
    })
    state["errors"] = errors[-20:]
    save(state)
