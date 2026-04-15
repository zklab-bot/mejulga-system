# content-engine/tests/test_integration_skills.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import build_system_prompt


def test_system_prompt_alma_contem_persona():
    prompt = build_system_prompt(["persona", "anti_persona", "codigo_julgamento"])
    assert "Dra. Julga" in prompt
    assert "culpado" in prompt.lower()
    assert "coach" in prompt.lower()  # anti-persona deve estar presente


def test_system_prompt_alma_nao_contem_placeholder():
    prompt = build_system_prompt(["persona", "anti_persona", "codigo_julgamento"])
    assert "TODO" not in prompt
    assert "TBD" not in prompt
    assert "[preencher]" not in prompt.lower()


def test_system_prompt_alma_tem_tamanho_razoavel():
    prompt = build_system_prompt(["persona", "anti_persona", "codigo_julgamento"])
    assert len(prompt) > 500
