import os
from engagement.shared import meta_client, claude_client, state


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def handle_dm(value: dict) -> None:
    """Processa evento de DM recebida e responde como Dra. Julga."""
    sender_id = value.get("sender", {}).get("id", "")
    text = value.get("message", {}).get("text", "").strip()

    if not sender_id or not text:
        return
    if sender_id == _account_id():
        return

    st = state.load()
    if sender_id in st.get("dms_replied", []):
        return

    resposta = claude_client.generate(
        f'Um seguidor te mandou uma DM: "{text}"\n\n'
        "Responda como Dra. Julga de forma simpática e curta (máximo 3 frases). "
        "Inclua o link mejulga.com.br para o diagnóstico completo. "
        "Seja engraçada e convidativa. Responda APENAS com o texto da mensagem.",
        max_tokens=200,
    )

    meta_client.post(
        f"{_account_id()}/messages",
        data={"recipient": {"id": sender_id}, "message": {"text": resposta}},
    )
    print(f"  ✅ DM respondida para {sender_id}")

    replied = st.setdefault("dms_replied", [])
    if sender_id not in replied:
        replied.append(sender_id)
    state.save(st)


def handle_comment(value: dict) -> None:
    """Processa evento de comentário novo e responde como Dra. Julga."""
    comment_id = value.get("id", "")
    text = value.get("text", "").strip()
    from_id = value.get("from", {}).get("id", "")

    if not comment_id or not text:
        return
    if from_id == _account_id():
        return

    st = state.load()
    if comment_id in st.get("comments_replied", []):
        return

    resposta = claude_client.generate(
        f'Um seguidor comentou no seu post: "{text}"\n\n'
        "Responda de forma curta (máximo 2 frases, até 150 caracteres). "
        "Seja engraçada e acolhedora. Máximo 2 emojis. "
        "Se mencionar um local (consultório, clínica, etc), use SEMPRE 'Tribunal Me Julga'. "
        "Responda APENAS com o texto da resposta.",
        max_tokens=150,
    )

    meta_client.post(f"{comment_id}/replies", data={"message": resposta})
    print(f"  ✅ Comentário {comment_id} respondido")

    replied = st.setdefault("comments_replied", [])
    if comment_id not in replied:
        replied.append(comment_id)
    state.save(st)
