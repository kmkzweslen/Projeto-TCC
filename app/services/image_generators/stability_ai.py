"""
Geração de imagem pela Stability AI (API Stable Image).

O endpoint v1 do SDXL (/v1/generation/stable-diffusion-xl-1024-v1-0) foi
substituído pela API Stable Image (v2beta). O endpoint é definido por
STABILITY_ENDPOINT no .env (padrão: Stable Image Core).
"""
import requests

from app.core import config
from app.services.http_utils import mensagem_de_erro

NOME = "Stability AI"


def disponivel() -> bool:
    return bool(config.STABILITY_API_KEY)


def modelo() -> str:
    return config.STABILITY_ENDPOINT.rstrip("/").rsplit("/", 1)[-1]


def gerar_imagem(prompt: str) -> bytes:
    """Gera uma imagem quadrada (1:1) e retorna seus bytes."""
    resposta = requests.post(
        config.STABILITY_ENDPOINT,
        headers={
            "Authorization": f"Bearer {config.STABILITY_API_KEY}",
            "Accept": "image/*",
        },
        files={"none": ""},
        data={
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "output_format": "jpeg",
        },
        timeout=config.IMAGE_TIMEOUT_S,
    )
    if not resposta.ok:
        raise RuntimeError(mensagem_de_erro(resposta))
    if not resposta.headers.get("Content-Type", "").startswith("image/"):
        raise RuntimeError("Resposta da Stability AI não contém imagem.")
    return resposta.content
