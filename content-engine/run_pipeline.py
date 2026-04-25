"""
Orquestrador do pipeline de carrossel da Dra. Julga.
Encadeia: generate_reels → render_slides → post_carrossel_instagram
Gerencia rotação de categorias sem repetição.
"""

import json, subprocess, sys, os
from pathlib import Path
from datetime import datetime

CATEGORIAS = ["amor", "dinheiro", "trabalho", "dopamina", "vida_adulta", "social", "saude_mental"]
STATE_FILE = Path(__file__).parent.parent / "category_state.json"
CONTENT_DIR = Path(__file__).parent

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"fila": [], "historico": []}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def next_categoria() -> str:
    state = load_state()
    if not state["fila"]:
        import random
        nova_fila = CATEGORIAS.copy()
        random.shuffle(nova_fila)
        state["fila"] = nova_fila
    categoria = state["fila"].pop(0)
    state["historico"].append({"categoria": categoria, "data": datetime.now().isoformat()})
    save_state(state)
    return categoria

def run(cmd: list, cwd: Path = None) -> int:
    print(f"\n▶ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or CONTENT_DIR, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"❌ Falhou com código {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode

def main():
    categoria = next_categoria()
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🎬 Pipeline: {categoria} — {hoje}")

    # Passo 1: Gerar roteiro
    run(["python", "generate_reels.py", "--categoria", categoria])

    # Passo 2: Renderizar slides via Playwright
    slides_dir = CONTENT_DIR / "generated" / "reels"
    payload = json.dumps({
        "roteiro": json.loads(
            sorted(slides_dir.glob(f"{hoje}_{categoria}_reels.json"))[-1].read_text(encoding="utf-8")
        ),
        "categoria": categoria,
        "pasta_saida": str(slides_dir)
    }, ensure_ascii=False)

    result = subprocess.run(
        ["node", str(CONTENT_DIR.parent / "render_slides.js")],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"❌ render_slides.js falhou:\n{result.stderr}")
        sys.exit(1)
    print(f"✅ Slides gerados: {result.stdout.strip()}")

    # Passo 3: Publicar no Instagram
    print("\n▶ python post_carrossel_instagram.py --categoria", categoria)
    result_post = subprocess.run(
        ["python", "post_carrossel_instagram.py", "--categoria", categoria, "--output-id"],
        capture_output=True, text=True, encoding="utf-8", cwd=CONTENT_DIR
    )
    if result_post.returncode != 0:
        print(f"❌ post_carrossel_instagram.py falhou:\n{result_post.stderr}")
        sys.exit(1)
    media_id = result_post.stdout.strip()
    print(f"✅ Publicado — media_id: {media_id}")

    # Passo 4: Comentário de engajamento
    if media_id:
        run(["python", "-m", "engagement.post_engagement",
             "--media_id", media_id, "--categoria", categoria])
    else:
        print("⚠️ media_id vazio — comentário de engajamento pulado")

    print(f"\n✅ Pipeline concluído: {categoria} — {hoje}")

if __name__ == "__main__":
    main()
