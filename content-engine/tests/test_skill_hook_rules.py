# content-engine/tests/test_skill_hook_rules.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import load_skill


def test_hook_rules_existe():
    content = load_skill("hook_rules")
    assert len(content) > 500


def test_hook_rules_contem_verdade_inconveniente():
    content = load_skill("hook_rules")
    assert "Verdade Inconveniente" in content
    for i in range(1, 9):
        assert f"V{i}" in content, f"Template V{i} não encontrado"


def test_hook_rules_contem_loop_curiosidade():
    content = load_skill("hook_rules")
    assert "Loop de Curiosidade" in content
    for i in range(1, 8):
        assert f"L{i}" in content, f"Template L{i} não encontrado"


def test_hook_rules_contem_combinadas():
    content = load_skill("hook_rules")
    assert "Combinad" in content
    for i in range(1, 7):
        assert f"C{i}" in content, f"Template C{i} não encontrado"


def test_hook_rules_contem_regra_rotacao():
    content = load_skill("hook_rules")
    assert "rotat" in content.lower() or "repetir" in content.lower()
