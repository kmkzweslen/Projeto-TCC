import base64

import pytest

from app.core import config
from app.services.image_generators import openai_image, stability_ai
from app.services.text_generators import gemini, gpt
from tests.conftest import RespostaFalsa


@pytest.fixture(autouse=True)
def chaves(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-teste")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "g-teste")
    monkeypatch.setattr(config, "STABILITY_API_KEY", "sk-stab")
    monkeypatch.setattr(config, "LLM_TEMPERATURE", None)


def test_openai_imagem_usa_gpt_image_e_decodifica_base64(monkeypatch):
    chamadas = {}

    def post(url, headers, json, timeout):
        chamadas.update(url=url, json=json)
        return RespostaFalsa(200, {"data": [{"b64_json": base64.b64encode(b"JPEGDATA").decode()}]})

    monkeypatch.setattr(openai_image.requests, "post", post)
    assert openai_image.gerar_imagem("um café") == b"JPEGDATA"
    assert chamadas["url"].endswith("/images/generations")
    assert chamadas["json"]["model"].startswith("gpt-image")
    assert chamadas["json"]["output_format"] == "jpeg"
    assert "quality" not in chamadas["json"]


def test_openai_texto_nao_envia_temperatura_por_padrao(monkeypatch):
    enviado = {}

    def post(url, headers, json, timeout):
        enviado.update(json)
        return RespostaFalsa(200, {"choices": [{"message": {"content": " Legenda pronta "}}]})

    monkeypatch.setattr(gpt.requests, "post", post)
    assert gpt.gerar_texto("prompt", "sistema") == "Legenda pronta"
    assert "temperature" not in enviado
    assert enviado["model"] == config.OPENAI_TEXT_MODEL != "gpt-3.5-turbo"
    assert enviado["messages"][0] == {"role": "system", "content": "sistema"}


def test_openai_texto_envia_temperatura_quando_configurada(monkeypatch):
    monkeypatch.setattr(config, "LLM_TEMPERATURE", 0.7)
    enviado = {}
    monkeypatch.setattr(gpt.requests, "post", lambda url, headers, json, timeout: (
        enviado.update(json) or RespostaFalsa(200, {"choices": [{"message": {"content": "ok"}}]})))
    gpt.gerar_texto("p", "s")
    assert enviado["temperature"] == 0.7


def test_erro_da_api_vira_mensagem_legivel(monkeypatch):
    monkeypatch.setattr(gpt.requests, "post", lambda *a, **k: RespostaFalsa(
        404, {"error": {"message": "The model does not exist"}}))
    with pytest.raises(RuntimeError, match="HTTP 404: The model does not exist"):
        gpt.gerar_texto("p", "s")


def test_gemini_tenta_fallback_quando_modelo_nao_existe(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_TEXT_MODEL", "gemini-inexistente")
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODELS", ["gemini-reserva"])
    urls = []

    def post(url, headers, json, timeout):
        urls.append(url)
        assert "generationConfig" not in json  # sem temperatura
        assert json["systemInstruction"]["parts"][0]["text"] == "s"
        if "inexistente" in url:
            return RespostaFalsa(404, {"error": {"message": "not found"}})
        return RespostaFalsa(200, {"candidates": [{"content": {"parts": [
            {"text": "pensando...", "thought": True}, {"text": "Legenda final"}]}}]})

    monkeypatch.setattr(gemini.requests, "post", post)
    assert gemini.gerar_texto("p", "s") == "Legenda final"
    assert len(urls) == 2 and gemini.modelo() == "gemini-reserva"


def test_gemini_bloqueado_gera_erro(monkeypatch):
    monkeypatch.setattr(gemini.requests, "post", lambda *a, **k: RespostaFalsa(
        200, {"candidates": [], "promptFeedback": {"blockReason": "SAFETY"}}))
    with pytest.raises(RuntimeError, match="SAFETY"):
        gemini.gerar_texto("p", "s")


def test_stability_usa_api_stable_image(monkeypatch):
    chamadas = {}

    def post(url, headers, files, data, timeout):
        chamadas.update(url=url, data=data, headers=headers)
        return RespostaFalsa(200, content=b"IMG", headers={"Content-Type": "image/jpeg"})

    monkeypatch.setattr(stability_ai.requests, "post", post)
    assert stability_ai.gerar_imagem("coffee") == b"IMG"
    assert "/v2beta/stable-image/generate/" in chamadas["url"]
    assert chamadas["data"]["output_format"] == "jpeg"
    assert chamadas["headers"]["Accept"] == "image/*"
