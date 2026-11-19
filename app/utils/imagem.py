"""
Tratamento de imagens para publicação no Instagram.

A Graph API aceita apenas JPEG, hospedado em URL pública. Este módulo baixa
(quando necessário), valida e converte qualquer imagem recebida dos provedores
para JPEG RGB.
"""
from io import BytesIO
from typing import Dict

import requests
from PIL import Image, UnidentifiedImageError

QUALIDADE_JPEG = 95
TIMEOUT_DOWNLOAD_S = 60


def baixar_bytes(url: str) -> bytes:
    resposta = requests.get(url, timeout=TIMEOUT_DOWNLOAD_S)
    resposta.raise_for_status()
    return resposta.content


def para_jpeg(conteudo: bytes) -> bytes:
    """
    Converte os bytes de uma imagem (PNG, WEBP, JPEG...) para JPEG RGB.
    Imagens com transparência recebem fundo branco.
    Lança ValueError se o conteúdo não for uma imagem válida.
    """
    try:
        imagem = Image.open(BytesIO(conteudo))
        imagem.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ValueError(f"Conteúdo recebido não é uma imagem válida: {e}") from e

    if imagem.mode in ("RGBA", "LA") or (imagem.mode == "P" and "transparency" in imagem.info):
        imagem = imagem.convert("RGBA")
        fundo = Image.new("RGB", imagem.size, (255, 255, 255))
        fundo.paste(imagem, mask=imagem.split()[-1])
        imagem = fundo
    elif imagem.mode != "RGB":
        imagem = imagem.convert("RGB")

    buffer = BytesIO()
    imagem.save(buffer, "JPEG", quality=QUALIDADE_JPEG, optimize=True)
    return buffer.getvalue()


def informacoes_imagem(conteudo: bytes) -> Dict:
    """Formato e dimensões da imagem (usado nos testes e nos registros)."""
    imagem = Image.open(BytesIO(conteudo))
    return {
        "formato": imagem.format,
        "modo": imagem.mode,
        "largura": imagem.width,
        "altura": imagem.height,
    }
