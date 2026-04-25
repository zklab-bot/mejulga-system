"""
Renderer HTML→PNG via Playwright.
Substitui o PIL para geração dos slides com qualidade de browser.
"""

import subprocess, json, sys, os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NODE_SCRIPT = REPO_ROOT / "render_slides.js"

def render_slides(roteiro: dict, categoria: str, pasta_saida: Path) -> list[Path]:
    """Chama o script Node que renderiza os slides via Playwright."""
    payload = json.dumps({
        "roteiro": roteiro,
        "categoria": categoria,
        "pasta_saida": str(pasta_saida)
    }, ensure_ascii=False)

    result = subprocess.run(
        ["node", str(NODE_SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO_ROOT)
    )

    if result.returncode != 0:
        raise RuntimeError(f"render_slides.js falhou:\n{result.stderr}")

    paths = json.loads(result.stdout.strip())
    return [Path(p) for p in paths]
