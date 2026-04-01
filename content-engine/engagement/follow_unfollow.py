"""
follow_unfollow.py
Segue contas do nicho e dessegue quem não retribuiu após 7 dias.

AVISO: Usa instagrapi (API privada do Instagram). Use com moderação.
Requer IG_USERNAME e IG_PASSWORD como variáveis de ambiente.

Uso:
  python -m engagement.follow_unfollow
  python -m engagement.follow_unfollow --dry-run
"""
import argparse
import os
from datetime import datetime, timedelta
from engagement.shared import state

MAX_FOLLOWS = 20
MAX_UNFOLLOWS = 20
UNFOLLOW_AFTER_DAYS = 7

HASHTAGS_NICHO = [
    "humorbrasileiro",
    "relacionamento",
    "terapia",
    "psicologia",
    "vidaadulta",
    "memesbrasil",
    "comportamento",
]


def _filtrar_candidatos(candidatos: list, following: dict) -> list:
    """Remove candidatos que já estão sendo seguidos."""
    return [uid for uid in candidatos if uid not in following]


def _candidatos_para_unfollow(following: dict, seguidores: set) -> list:
    """Retorna IDs seguidos há mais de UNFOLLOW_AFTER_DAYS que não seguiram de volta."""
    corte = datetime.now() - timedelta(days=UNFOLLOW_AFTER_DAYS)
    return [
        uid for uid, ts in following.items()
        if datetime.fromisoformat(ts) < corte and uid not in seguidores
    ]


def executar(dry_run: bool = False) -> None:
    print(f"\n👥 Follow/Unfollow — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("⚠️  Usa API privada — execute com moderação\n")

    try:
        from instagrapi import Client
    except ImportError:
        print("❌ instagrapi não instalado. Execute: pip install instagrapi")
        return

    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    if not username or not password:
        print("❌ IG_USERNAME e IG_PASSWORD não configurados")
        return

    st = state.load()
    following: dict = st.setdefault("following", {})

    cl = None
    if not dry_run:
        cl = Client()
        cl.login(username, password)
        print(f"  ✅ Login como @{username}")

    # --- Fase FOLLOW ---
    hashtag = HASHTAGS_NICHO[datetime.now().weekday() % len(HASHTAGS_NICHO)]
    print(f"  🔍 Buscando candidatos em #{hashtag}...")

    candidatos_raw: list[str] = []
    if not dry_run and cl:
        medias = cl.hashtag_medias_recent(hashtag, amount=60)
        candidatos_raw = [str(m.user.pk) for m in medias]
    else:
        print(f"  [DRY RUN] Buscaria em #{hashtag}")
        candidatos_raw = ["fake_user_1", "fake_user_2"]

    candidatos = _filtrar_candidatos(candidatos_raw, following)[:MAX_FOLLOWS]
    follows = 0
    for uid in candidatos:
        if follows >= MAX_FOLLOWS:
            break
        if dry_run:
            print(f"  [DRY RUN] Seguiria {uid}")
        else:
            cl.user_follow(int(uid))
            print(f"  ✅ Seguiu {uid}")
        following[uid] = datetime.now().isoformat()
        follows += 1

    # --- Fase UNFOLLOW ---
    print(f"\n  🔍 Verificando quem não seguiu de volta...")
    seguidores: set = set()
    if not dry_run and cl:
        meu_id = cl.user_id
        seguidores = {str(u.pk) for u in cl.user_followers(meu_id).values()}

    para_desseguir = _candidatos_para_unfollow(following, seguidores)[:MAX_UNFOLLOWS]
    unfollows = 0
    for uid in para_desseguir:
        if unfollows >= MAX_UNFOLLOWS:
            break
        if dry_run:
            print(f"  [DRY RUN] Desseguiria {uid}")
        else:
            cl.user_unfollow(int(uid))
            print(f"  ✅ Desseguiu {uid}")
        del following[uid]
        unfollows += 1

    st["following"] = following
    state.save(st)
    print(f"\n✅ {follows} follow(s), {unfollows} unfollow(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
