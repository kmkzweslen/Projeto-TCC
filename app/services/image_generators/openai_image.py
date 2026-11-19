"""
Geração de imagem pela OpenAI (Images API, família GPT Image).

A família DALL·E foi retirada da API em 12/05/2026. Os modelos GPT Image
devolvem a imagem em base64 (b64_json), e não mais por URL temporária.
O modelo é definido por OPENAI_IMAGE_MODEL no .env.
"""
import base64

import requests

from app.core import config
from app.services.http_utils import mensagem_de_erro

NOME = "OpenAI Images"


def disponivel() -> bool:
    return bool(config.OPENAI_API_KEY)


def modelo() -> str:
    return config.OPENAI_IMAGE_MODEL


def gerar_imagem(prompt: str) -> bytes:
    """Gera uma imagem e retorna seus bytes. Lança RuntimeError em caso de falha."""
    corpo = {
        "model": config.OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "size": config.OPENAI_IMAGE_SIZE,
        "n": 1,
        "output_format": "jpeg",
    }
    if config.OPENAI_IMAGE_QUALITY:
        corpo["quality"] = config.OPENAI_IMAGE_QUALITY

    resposta = requests.post(
        f"{config.OPENAI_BASE_URL}/images/generations",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        json=corpo,
        timeout=config.IMAGE_TIMEOUT_S,
    )
    if not resposta.ok:
        raise RuntimeError(mensagem_de_erro(resposta))

    dados = (resposta.json().get("data") or [{}])[0]
    if dados.get("b64_json"):
        return base64.b64decode(dados["b64_json"])
    if dados.get("url"):  # compatibilidade com modelos que ainda retornam URL
        download = requests.get(dados["url"], timeout=config.IMAGE_TIMEOUT_S)
        download.raise_for_status()
        return download.content
    raise RuntimeError("Resposta da OpenAI sem imagem (b64_json/url ausentes).")
