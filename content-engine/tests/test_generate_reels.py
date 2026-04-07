# content-engine/tests/test_generate_reels.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import generate_reels as gr


def _roteiro_valido():
    """Fixture: roteiro mínimo válido para testes."""
    return {
        "categoria": "amor",
        "titulo": "O Sumido Saudoso",
        "numero_processo": "AMO-001/26",
        "crime": "ghosting sazonal com dolo comprovado",
        "tipo_veredicto": "A",
        "frase_printavel": "Culpado por ghosting sazonal. Sem apelação.",
        "cenas": [
            {"numero": 1, "duracao_segundos": 3,
             "texto": "3 meses sem dar um pio. Agora voltou com 'oi sumida'.",
             "texto_slide": "3 meses de silêncio.\n'Oi sumida' às 23h."},
            {"numero": 2, "duracao_segundos": 4,
             "texto": "O réu deixou 47 mensagens no vácuo entre abril e julho.",
             "texto_slide": "47 mensagens.\nTodas lidas. Zero respostas."},
            {"numero": 3, "duracao_segundos": 4,
             "texto": "Enquanto isso, curtiu 12 stories seus. Sem responder nenhum.",
             "texto_slide": "12 stories curtidos.\nNenhuma palavra."},
            {"numero": 4, "duracao_segundos": 4,
             "texto": "Agravante: ele voltou numa sexta às 23h47. Clássico.",
             "texto_slide": "Sexta, 23h47.\nAgravante confirmado."},
            {"numero": 5, "duracao_segundos": 4,
             "texto": "VEREDICTO: Culpado por ghosting sazonal com dolo comprovado. Sem apelação.",
             "texto_slide": "VEREDICTO\nCulpado por ghosting sazonal.\nSem apelação."},
            {"numero": 6, "duracao_segundos": 3,
             "texto": "Veja seu processo em mejulga.com.br",
             "texto_slide": "Veja seu processo.\nmejulga.com.br"},
        ],
        "texto_completo": "3 meses sem dar um pio...",
        "legenda_instagram": "#draJulga",
        "sugestao_musica": "lo-fi tenso",
    }


def test_validar_roteiro_valido_retorna_none():
    assert gr._validar_roteiro(_roteiro_valido()) is None


def test_validar_roteiro_rejeita_slide_igual_texto():
    r = _roteiro_valido()
    r["cenas"][1]["texto_slide"] = r["cenas"][1]["texto"]
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "redundante" in resultado.lower()


def test_validar_roteiro_rejeita_abertura_gente():
    r = _roteiro_valido()
    r["cenas"][0]["texto"] = "Gente, vocês fazem isso?"
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "gente" in resultado.lower()


def test_validar_roteiro_rejeita_diagnostico():
    r = _roteiro_valido()
    r["cenas"][4]["texto"] = "Diagnóstico: síndrome do amor ausente."
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "diagnóstico" in resultado.lower()


def test_validar_roteiro_rejeita_veredicto_longo():
    r = _roteiro_valido()
    # cena 5 com mais de 20 palavras
    r["cenas"][4]["texto"] = (
        "VEREDICTO: Culpado por uma série de comportamentos extremamente duvidosos "
        "e questionáveis que demonstram total desrespeito pelas outras pessoas. Sem apelação."
    )
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "veredicto" in resultado.lower()


def test_calcular_numero_processo_sem_arquivos(tmp_path):
    resultado = gr._calcular_numero_processo("amor", tmp_path)
    assert resultado == "AMO-001/26"


def test_calcular_numero_processo_com_arquivos_existentes(tmp_path):
    # Simula 2 posts anteriores de amor
    (tmp_path / "2026-04-01_amor_reels.json").write_text("{}")
    (tmp_path / "2026-04-03_amor_reels.json").write_text("{}")
    resultado = gr._calcular_numero_processo("amor", tmp_path)
    assert resultado == "AMO-003/26"


def test_calcular_numero_processo_nao_conta_outras_categorias(tmp_path):
    (tmp_path / "2026-04-01_amor_reels.json").write_text("{}")
    (tmp_path / "2026-04-02_trabalho_reels.json").write_text("{}")
    resultado = gr._calcular_numero_processo("amor", tmp_path)
    assert resultado == "AMO-002/26"


def test_sorteio_veredicto_retorna_valor_valido():
    for _ in range(20):
        resultado = gr._sorteio_veredicto()
        assert resultado in ("A", "B", "C")


def test_gerar_roteiro_retenta_quando_invalido(monkeypatch, tmp_path):
    """Verifica que gerar_roteiro tenta novamente quando a validação falha."""
    roteiro_ruim = _roteiro_valido()
    roteiro_ruim["cenas"][0]["texto"] = "Gente, isso é um teste."  # inválido

    roteiro_bom = _roteiro_valido()

    chamadas = []

    def mock_create(**kwargs):
        chamadas.append(kwargs)
        r = roteiro_ruim if len(chamadas) == 1 else roteiro_bom
        mock_resp = MagicMock()
        mock_resp.content[0].text = json.dumps(r)
        return mock_resp

    monkeypatch.setattr(gr.claude_client.messages, "create", mock_create)

    resultado = gr.gerar_roteiro("amor", tipo_veredicto="A", pasta=tmp_path)

    assert len(chamadas) == 2  # tentou 2 vezes
    assert resultado["cenas"][0]["texto"] == roteiro_bom["cenas"][0]["texto"]


def test_gerar_roteiro_retorna_mesmo_invalido_apos_2_tentativas(monkeypatch, tmp_path):
    """Após 2 falhas, retorna o último roteiro sem travar."""
    roteiro_ruim = _roteiro_valido()
    roteiro_ruim["cenas"][0]["texto"] = "Gente, sempre inválido."

    def mock_create(**kwargs):
        mock_resp = MagicMock()
        mock_resp.content[0].text = json.dumps(roteiro_ruim)
        return mock_resp

    monkeypatch.setattr(gr.claude_client.messages, "create", mock_create)

    resultado = gr.gerar_roteiro("amor", tipo_veredicto="A", pasta=tmp_path)
    # Não levanta exceção — retorna o roteiro mesmo inválido
    assert resultado is not None
