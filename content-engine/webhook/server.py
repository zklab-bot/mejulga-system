import os
from contextlib import asynccontextmanager

import requests as http
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from webhook.signature import verify_signature
from webhook import handlers
from webhook import telegram_handler

load_dotenv()

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")

# Slots UTC → BRT: 12h=09h, 15h=12h, 21h=18h, 23h=20h, 01h=22h
_POST_SLOTS_UTC = [12, 15, 21, 23, 1]


def _trigger_daily_post() -> None:
    pat = os.getenv("GITHUB_PAT", "")
    if not pat:
        print("[scheduler] GITHUB_PAT nao configurado — post nao disparado")
        return
    url = "https://api.github.com/repos/zklab-bot/mejulga-system/actions/workflows/daily_post.yml/dispatches"
    resp = http.post(
        url,
        headers={"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"},
        json={"ref": "main", "inputs": {}},
        timeout=15,
    )
    if resp.status_code == 204:
        print("[scheduler] daily_post.yml disparado")
    else:
        print(f"[scheduler] Erro ao disparar: {resp.status_code} {resp.text[:200]}")


_scheduler = AsyncIOScheduler(timezone="UTC")
for _h in _POST_SLOTS_UTC:
    _scheduler.add_job(_trigger_daily_post, CronTrigger(hour=_h, minute=0, timezone="UTC"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _scheduler.start()
    slots_brt = ["09h", "12h", "18h", "20h", "22h"]
    print(f"[scheduler] iniciado — posts agendados: {', '.join(slots_brt)} BRT")
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


@app.get("/webhook")
async def handshake(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))
    return Response(status_code=403)


@app.post("/webhook")
async def receive(request: Request):
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256", "")

    if not verify_signature(body, sig, APP_SECRET):
        return Response(status_code=401)

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    for entry in payload.get("entry", []):
        for msg_event in entry.get("messaging", []):
            handlers.handle_dm(msg_event)

        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})
            if field == "messages":
                handlers.handle_dm(value)
            elif field == "comments":
                handlers.handle_comment(value)

    return {"status": "ok"}


@app.post("/telegram")
async def telegram(request: Request):
    telegram_secret = os.getenv("TELEGRAM_SECRET", "")
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not telegram_secret or secret != telegram_secret:
        return Response(status_code=403)

    try:
        update = await request.json()
    except Exception:
        return {"ok": True}

    telegram_handler.handle(update)
    return {"ok": True}
