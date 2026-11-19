"""
Geração de legenda pela OpenAI (Chat Completions).

O gpt-3.5-turbo foi desligado em 23/10/2026; o modelo é definido por
OPENAI_TEXT_MODEL no .env. Os modelos GPT-5.x só aceitam a temperatura
padrão, por isso ela só é enviada quando LLM_TEMPERATURE for definido.
"""
import requests

from app.core import config
from app.services.http_utils import mensagem_de_erro

NOME = "OpenAI GPT"


def disponivel() -> bool:
    return bool(config.OPENAI_API_KEY)


def modelo() -> str:
    return config.OPENAI_TEXT_MODEL


def gerar_texto(prompt: str, sistema: str) -> str:
    corpo = {
        "model": config.OPENAI_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": prompt},
        ],
    }
    if config.LLM_TEMPERATURE is not None:
        corpo["temperature"] = config.LLM_TEMPERATURE

    resposta = requests.post(
        f"{config.OPENAI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        json=corpo,
        timeout=config.TEXT_TIMEOUT_S,
    )
    if not resposta.ok:
        raise RuntimeError(mensagem_de_erro(resposta))

    escolhas = resposta.json().get("choices") or []
    texto = ((escolhas[0].get("message") or {}).get("content") if escolhas else None) or ""
    if not texto.strip():
        raise RuntimeError("A OpenAI retornou uma resposta vazia.")
    return texto.strip()
