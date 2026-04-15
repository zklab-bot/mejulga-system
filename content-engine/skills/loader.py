# content-engine/skills/loader.py
from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def load_skill(skill_name: str) -> str:
    """Carrega um arquivo de skill pelo nome (sem extensão .md)."""
    path = SKILLS_DIR / f"{skill_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill não encontrada: {path}")
    return path.read_text(encoding="utf-8")


def build_system_prompt(skills: list) -> str:
    """Assembla múltiplas skills em um único system prompt."""
    if not skills:
        return ""
    parts = [load_skill(name) for name in skills]
    return "\n\n---\n\n".join(parts)
