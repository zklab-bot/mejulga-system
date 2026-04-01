import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://graph.facebook.com/v19.0"
_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
MAX_RETRIES = 3
BACKOFF_BASE = 2


class MetaAPIError(Exception):
    pass


class MetaPermissionError(MetaAPIError):
    pass


class MetaRateLimitError(MetaAPIError):
    pass


def _request(method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    p = dict(params or {})
    p["access_token"] = os.getenv("META_ACCESS_TOKEN") or _ACCESS_TOKEN

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(method, url, params=p, data=data, timeout=30)
            body = resp.json()

            if resp.status_code == 200:
                return body

            error = body.get("error", {})
            code = error.get("code")

            if code == 32:
                raise MetaRateLimitError(
                    f"Rate limit atingido: {error.get('message')}"
                )
            if code in (10, 200):
                raise MetaPermissionError(
                    f"Permissão negada (code={code}). "
                    f"Verifique o App Review da Meta. Mensagem: {error.get('message')}"
                )

            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** attempt)
                continue

            raise MetaAPIError(f"Erro {resp.status_code}: {body}")

        except (MetaRateLimitError, MetaPermissionError):
            raise
        except MetaAPIError:
            if attempt == MAX_RETRIES - 1:
                raise
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise MetaAPIError(f"Erro de rede: {e}") from e
            time.sleep(BACKOFF_BASE ** attempt)

    raise MetaAPIError("Máximo de tentativas atingido")


def get(endpoint: str, params: dict = None) -> dict:
    return _request("GET", endpoint, params=params)


def post(endpoint: str, data: dict = None) -> dict:
    return _request("POST", endpoint, data=data)
