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
        "e questionáveis que demonstram total falta de respeito pelas outras pessoas. Sem apelação."
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


def _post_details_com_notas(notas_a, notas_b, notas_c):
    """Cria post_details com notas sintéticas por variação."""
    details = {}
    for i, nota in enumerate(notas_a):
        details[f"data_a_{i}_amor"] = {"tipo_veredicto": "A", "nota": nota}
    for i, nota in enumerate(notas_b):
        details[f"data_b_{i}_amor"] = {"tipo_veredicto": "B", "nota": nota}
    for i, nota in enumerate(notas_c):
        details[f"data_c_{i}_amor"] = {"tipo_veredicto": "C", "nota": nota}
    return details


def test_calcular_pesos_retorna_base_sem_dados():
    assert gr._calcular_pesos_veredicto({}) == [60, 25, 15]


def test_calcular_pesos_retorna_base_com_dados_insuficientes():
    # Variação B com apenas 2 notas — não ativa ajuste
    details = _post_details_com_notas([4, 5, 4], [3, 3], [3, 3, 3])
    assert gr._calcular_pesos_veredicto(details) == [60, 25, 15]


def test_calcular_pesos_ajustados_soma_100():
    details = _post_details_com_notas([4, 5, 4], [2, 2, 3], [3, 3, 3])
    pesos = gr._calcular_pesos_veredicto(details)
    assert sum(pesos) == 100


def test_calcular_pesos_a_favorecida_quando_notas_altas():
    # A muito melhor que B e C
    details = _post_details_com_notas([5, 5, 5], [1, 1, 1], [1, 1, 1])
    pesos = gr._calcular_pesos_veredicto(details)
    assert pesos[0] > pesos[1]
    assert pesos[0] > pesos[2]


def test_calcular_pesos_nenhuma_variacao_abaixo_de_5():
    # Variação C com notas muito baixas
    details = _post_details_com_notas([5, 5, 5], [5, 5, 5], [1, 1, 1])
    pesos = gr._calcular_pesos_veredicto(details)
    assert all(p >= 5 for p in pesos)


def test_calcular_pesos_usa_apenas_ultimas_10_notas():
    # A tem 12 notas: 9 ruins + últimas 3 boas
    notas_a = [1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5]
    notas_b = [3, 3, 3]
    notas_c = [3, 3, 3]
    details_12 = _post_details_com_notas(notas_a, notas_b, notas_c)
    pesos_12 = gr._calcular_pesos_veredicto(details_12)

    # A com exatamente as últimas 10 notas: [1,1,1,1,1,1,1,5,5,5] → média 2.7
    notas_a_10 = [1, 1, 1, 1, 1, 1, 1, 5, 5, 5]
    details_10 = _post_details_com_notas(notas_a_10, notas_b, notas_c)
    pesos_10 = gr._calcular_pesos_veredicto(details_10)

    assert pesos_12 == pesos_10


def test_calcular_pesos_exemplo_do_spec():
    # Spec: A=[4,5,4] B=[2,2,3] C=[3,3,3] → A=72, B=16, C=12
    details = _post_details_com_notas([4, 5, 4], [2, 2, 3], [3, 3, 3])
    pesos = gr._calcular_pesos_veredicto(details)
    assert pesos == [72, 16, 12]


def test_sorteio_veredicto_usa_post_details(monkeypatch):
    # Com A dominante, A deve ser sorteado na maioria das vezes
    details = _post_details_com_notas([5, 5, 5], [1, 1, 1], [1, 1, 1])
    resultados = [gr._sorteio_veredicto(details) for _ in range(50)]
    assert resultados.count("A") > 30  # alta concentração em A


def test_system_prompt_contem_tipos_de_ancoragem():
    """SYSTEM_PROMPT deve listar os 6 tipos de ancoragem."""
    for tipo in ["HORÁRIO", "QUANTIDADE", "PLATAFORMA", "CITAÇÃO", "COMPARAÇÃO", "COMPORTAMENTO"]:
        assert tipo in gr.SYSTEM_PROMPT, f"SYSTEM_PROMPT não contém tipo de ancoragem: {tipo}"


def test_system_prompt_proibe_ancoragem_consecutiva():
    """SYSTEM_PROMPT deve mencionar a proibição de tipos consecutivos."""
    assert "duas cenas seguidas" in gr.SYSTEM_PROMPT


def test_system_prompt_contem_angulos_narrativos():
    """SYSTEM_PROMPT deve conter a seção de ângulos narrativos."""
    assert "ÂNGULOS NARRATIVOS" in gr.SYSTEM_PROMPT


def test_system_prompt_angulos_tem_exemplos():
    """ÂNGULOS NARRATIVOS deve listar pelo menos FORENSE e SOCIOLÓGICO."""
    assert "FORENSE" in gr.SYSTEM_PROMPT
    assert "SOCIOLÓGICO" in gr.SYSTEM_PROMPT


# ── Glossário ──────────────────────────────────────────────────────────────────

def _glossario_valido():
    """Fixture: glossário mínimo válido para testes."""
    return {
        "formato_post": "glossario",
        "categoria": "amor",
        "termo": "afetofobia seletiva",
        "pronuncia": "a·fe·to·fo·bi·a  se·le·ti·va",
        "classe_gramatical": "substantivo feminino",
        "definicao": "Incapacidade de demonstrar afeto — mas só com quem gosta de verdade.",
        "manifestacao": "Sumiços estratégicos. Mensagens frias logo depois de noites boas.",
        "nao_confundir": "Não confundir com timidez. Tímido não some. Tímido demora.",
        "frase_exemplo": "Ele só é assim comigo. Com os outros ele é super carinhoso.",
        "veredicto": "Culpado de fugir do que mais quer. Pena: ficar com quem não teme.",
        "legenda_instagram": "#draJulga #glossario",
        "sugestao_musica": "lo-fi introspectivo",
    }


def test_validar_glossario_valido_retorna_none():
    assert gr._validar_glossario(_glossario_valido()) is None


def test_validar_glossario_rejeita_campo_ausente():
    g = _glossario_valido()
    del g["definicao"]
    resultado = gr._validar_glossario(g)
    assert resultado is not None
    assert "definicao" in resultado


def test_validar_glossario_rejeita_jargao_medico():
    g = _glossario_valido()
    g["definicao"] = "Síndrome do abandono afetivo crônico."
    resultado = gr._validar_glossario(g)
    assert resultado is not None
    assert "síndrome" in resultado.lower()


def test_validar_glossario_rejeita_veredicto_longo():
    g = _glossario_valido()
    g["veredicto"] = "Culpado de uma série de comportamentos extremamente duvidosos que demonstram total falta de capacidade de amar alguém de verdade sem fugir desesperadamente de tudo que é bom e genuíno na vida."
    resultado = gr._validar_glossario(g)
    assert resultado is not None
    assert "veredicto" in resultado.lower()


def test_gerar_glossario_chama_api_e_retorna_dict(monkeypatch, tmp_path):
    glossario_mock = _glossario_valido()

    def mock_create(**kwargs):
        mock_resp = MagicMock()
        mock_resp.content[0].text = json.dumps(glossario_mock)
        return mock_resp

    monkeypatch.setattr(gr.claude_client.messages, "create", mock_create)
    resultado = gr.gerar_glossario("amor", pasta=tmp_path)

    assert resultado["formato_post"] == "glossario"
    assert resultado["termo"] == "afetofobia seletiva"


def test_salvar_glossario_cria_json(tmp_path):
    g = _glossario_valido()
    arquivo = gr.salvar_glossario(g, tmp_path)
    assert arquivo.exists()
    with open(arquivo, encoding="utf-8") as f:
        data = json.load(f)
    assert data["termo"] == g["termo"]
