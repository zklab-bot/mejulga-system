import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from webhook.signature import verify_signature
from webhook import handlers
from webhook import telegram_handler

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
TELEGRAM_SECRET = os.getenv("TELEGRAM_SECRET", "")


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
        # Formato Messenger: entry[].messaging[] (DMs do Instagram)
        for msg_event in entry.get("messaging", []):
            handlers.handle_dm(msg_event)

        # Formato Instagram Webhooks: entry[].changes[] (comentários, menções)
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
