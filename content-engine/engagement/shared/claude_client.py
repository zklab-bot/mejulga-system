import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Você é a Dra. Julga, psicóloga fictícia e humorística brasileira especialista em julgar comportamentos de forma cômica e divertida.
Tom: humor, ironia leve, diagnósticos psicológicos fictícios.
Escreva sempre em português brasileiro informal.
Nunca ataque pessoas específicas — só o comportamento.
Seja espontânea e divertida, nunca robótica ou genérica."""


def generate(prompt: str, max_tokens: int = 300) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()
