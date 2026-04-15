# content-engine/tests/test_skills_loader.py
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import load_skill, build_system_prompt


def test_load_skill_retorna_string_nao_vazia(tmp_path, monkeypatch):
    skill_file = tmp_path / "test_skill.md"
    skill_file.write_text("# Test Skill\nConteúdo de teste.", encoding="utf-8")
    monkeypatch.setattr("skills.loader.SKILLS_DIR", tmp_path)
    result = load_skill("test_skill")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Conteúdo de teste." in result


def test_load_skill_arquivo_inexistente_lanca_erro(tmp_path, monkeypatch):
    monkeypatch.setattr("skills.loader.SKILLS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="Skill não encontrada"):
        load_skill("skill_que_nao_existe")


def test_build_system_prompt_combina_skills(tmp_path, monkeypatch):
    (tmp_path / "skill_a.md").write_text("# Skill A\nConteúdo A.", encoding="utf-8")
    (tmp_path / "skill_b.md").write_text("# Skill B\nConteúdo B.", encoding="utf-8")
    monkeypatch.setattr("skills.loader.SKILLS_DIR", tmp_path)
    prompt = build_system_prompt(["skill_a", "skill_b"])
    assert "Conteúdo A." in prompt
    assert "Conteúdo B." in prompt
    assert "---" in prompt


def test_build_system_prompt_lista_vazia_retorna_vazio(tmp_path, monkeypatch):
    monkeypatch.setattr("skills.loader.SKILLS_DIR", tmp_path)
    result = build_system_prompt([])
    assert result == ""
