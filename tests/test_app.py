import html
import json
import os
import sys
from unittest.mock import patch

import pytest

# Garante a importação de app.py a partir da raiz do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as extrator


@pytest.fixture
def client():
    extrator.app.config["TESTING"] = True
    with extrator.app.test_client() as test_client:
        yield test_client


def test_limpar_json_valido_direto():
    bruto = '{"categoria": "Combustivel", "valor": 50.0, "descricao": "etanol"}'
    limpo = extrator.limpar_json(bruto)
    assert json.loads(limpo) == {
        "categoria": "Combustivel",
        "valor": 50.0,
        "descricao": "etanol",
    }


def test_limpar_json_remove_think_e_markdown():
    bruto = '<think>analisando texto...</think>\n```json\n{"despesas": []}\n```'
    limpo = extrator.limpar_json(bruto)
    assert json.loads(limpo) == {"despesas": []}


def test_limpar_json_extrai_ultimo_objeto_em_texto_misturado():
    bruto = (
        'Thinking Process: primeiro pensei em {"despesas": []}. '
        'Resultado final: {"despesas": [{"categoria": "Alimentacao", "valor": 25.0, "descricao": "marmitex"}]}'
    )
    limpo = extrator.limpar_json(bruto)
    assert json.loads(limpo) == {
        "despesas": [
            {"categoria": "Alimentacao", "valor": 25.0, "descricao": "marmitex"}
        ]
    }


def test_limpar_json_vazio_ou_sem_json():
    assert extrator.limpar_json("") == ""
    assert extrator.limpar_json("resposta sem objeto json") == ""


def test_obter_config_ssl(monkeypatch):
    monkeypatch.setenv("LLM_CA_BUNDLE", "false")
    assert extrator.obter_config_ssl() is False

    monkeypatch.setenv("LLM_CA_BUNDLE", "true")
    assert extrator.obter_config_ssl() is True

    monkeypatch.setenv("LLM_CA_BUNDLE", "/certs/ca-interno.pem")
    assert extrator.obter_config_ssl() == "/certs/ca-interno.pem"


@pytest.mark.parametrize("entrada", ["", "     ", "\t\n"])
def test_post_bloqueia_entrada_vazia_ou_espacos(client, entrada):
    with patch.object(extrator, "consultar_llm") as mock_llm:
        resp = client.post("/", data={"gasto": entrada})
        body = html.unescape(resp.get_data(as_text=True))

        assert resp.status_code == 200
        assert "Por favor, descreva o gasto antes de enviar." in body
        mock_llm.assert_not_called()


def test_post_extracao_multipla_simulada(client):
    payload_mock = json.dumps(
        {
            "despesas": [
                {"categoria": "Alimentacao", "valor": 25.0, "descricao": "marmitex"},
                {"categoria": "Combustivel", "valor": 100.0, "descricao": "etanol"},
            ]
        }
    )

    with patch.object(extrator, "consultar_llm", return_value=payload_mock) as mock_llm:
        resp = client.post(
            "/", data={"gasto": "gastei 25 reais num marmitex e 100 conto de etanol"}
        )
        body = html.unescape(resp.get_data(as_text=True))

        assert resp.status_code == 200
        assert '"categoria": "Alimentacao"' in body
        assert '"valor": 25.0' in body
        assert '"categoria": "Combustivel"' in body
        assert '"valor": 100.0' in body
        mock_llm.assert_called_once()


def test_post_sem_despesas_simulada(client):
    with patch.object(extrator, "consultar_llm", return_value='{"despesas": []}'):
        resp = client.post("/", data={"gasto": "ola bom dia tudo bem?"})
        body = html.unescape(resp.get_data(as_text=True))

        assert resp.status_code == 200
        assert '"despesas": []' in body


def test_post_resposta_vazia_llm(client):
    with patch.object(extrator, "consultar_llm", return_value=""):
        resp = client.post("/", data={"gasto": "abasteci 50 de etanol"})
        body = html.unescape(resp.get_data(as_text=True))

        assert resp.status_code == 200
        assert "A LLM retornou uma resposta vazia. Envie novamente." in body


def test_post_mascaramento_excecao_generica(client):
    with patch.object(
        extrator, "consultar_llm", side_effect=RuntimeError("detalhe interno sensivel")
    ):
        resp = client.post("/", data={"gasto": "abasteci 50 de etanol"})
        body = html.unescape(resp.get_data(as_text=True))

        assert resp.status_code == 200
        assert "Ocorreu um erro inesperado ao comunicar com o serviço." in body
        assert "detalhe interno sensivel" not in body