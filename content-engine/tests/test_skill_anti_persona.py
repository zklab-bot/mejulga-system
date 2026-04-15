# content-engine/tests/test_skill_anti_persona.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import load_skill


def test_anti_persona_existe_e_tem_conteudo():
    content = load_skill("anti_persona")
    assert len(content) > 200


def test_anti_persona_lista_proibicoes():
    content = load_skill("anti_persona")
    assert "coach" in content.lower()
    assert "conselho" in content.lower() or "aconselh" in content.lower()
    assert "moraliza" in content.lower() or "moral" in content.lower()


def test_anti_persona_tem_exemplos_errado_certo():
    content = load_skill("anti_persona")
    assert "❌" in content
    assert "✅" in content
