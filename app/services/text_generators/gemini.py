"""
Geração de legenda pelo Google Gemini (REST generateContent).

A família Gemini 1.5 foi retirada. O modelo é definido por GEMINI_TEXT_MODEL;
se ele não existir (HTTP 404), são tentados os modelos de GEMINI_FALLBACK_MODELS.
A partir do Gemini 3.6, temperature/top_p/top_k não devem ser enviados, por
isso a temperatura só vai na requisição quando LLM_TEMPERATURE for definido.
"""
import requests

from app.core import config
from app.services.http_utils import mensagem_de_erro

NOME = "Google Gemini"

# Modelo efetivamente usado na última chamada (para registro na resposta).
_ultimo_modelo = {"nome": None}


def disponivel() -> bool:
    return bool(config.GEMINI_API_KEY)


def modelo() -> str:
    return _ultimo_modelo["nome"] or config.GEMINI_TEXT_MODEL


def _extrair_texto(dados: dict) -> str:
    candidatos = dados.get("candidates") or []
    if not candidatos:
        bloqueio = (dados.get("promptFeedback") or {}).get("blockReason")
        raise RuntimeError(f"O Gemini não retornou candidatos (bloqueio: {bloqueio}).")
    partes = ((candidatos[0].get("content") or {}).get("parts")) or []
    texto = "".join(p.get("text", "") for p in partes if not p.get("thought"))
    if not texto.strip():
        motivo = candidatos[0].get("finishReason")
        raise RuntimeError(f"O Gemini retornou uma resposta vazia (finishReason: {motivo}).")
    return texto.strip()


def gerar_texto(prompt: str, sistema: str) -> str:
    corpo = {
        "systemInstruction": {"parts": [{"text": sistema}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    if config.LLM_TEMPERATURE is not None:
        corpo["generationConfig"] = {"temperature": config.LLM_TEMPERATURE}

    modelos = [config.GEMINI_TEXT_MODEL] + [
        m for m in config.GEMINI_FALLBACK_MODELS if m != config.GEMINI_TEXT_MODEL
    ]
    ultimo_erro = "nenhum modelo configurado"
    for nome_modelo in modelos:
        resposta = requests.post(
            f"{config.GEMINI_BASE_URL}/models/{nome_modelo}:generateContent",
            headers={"x-goog-api-key": config.GEMINI_API_KEY},
            json=corpo,
            timeout=config.TEXT_TIMEOUT_S,
        )
        if resposta.status_code == 404:
            ultimo_erro = f"modelo '{nome_modelo}' não encontrado"
            continue
        if not resposta.ok:
            raise RuntimeError(mensagem_de_erro(resposta))
        _ultimo_modelo["nome"] = nome_modelo
        return _extrair_texto(resposta.json())

    raise RuntimeError(f"Nenhum modelo Gemini disponível ({ultimo_erro}).")
