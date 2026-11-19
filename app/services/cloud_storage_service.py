"""
Hospedagem pública das imagens (ImgBB).

A Graph API busca a imagem por URL no momento da publicação, então ela
precisa estar em um servidor publicamente acessível.
"""
import base64
from typing import Dict

import requests

from app.core import config
from app.utils.imagem import para_jpeg

IMGBB_URL = "https://api.imgbb.com/1/upload"
TIMEOUT_UPLOAD_S = 60


class ErroHospedagem(Exception):
    pass


def hospedar_imagem(conteudo: bytes) -> Dict:
    """
    Converte a imagem para JPEG e envia ao ImgBB.
    Retorna um dicionário com 'public_url' e metadados do upload.
    """
    if not config.IMGBB_API_KEY:
        raise ErroHospedagem("IMGBB_API_KEY não configurada no .env")

    jpeg = para_jpeg(conteudo)

    try:
        resposta = requests.post(
            IMGBB_URL,
            data={
                "key": config.IMGBB_API_KEY,
                "image": base64.b64encode(jpeg).decode(),
            },
            timeout=TIMEOUT_UPLOAD_S,
        )
        resultado = resposta.json()
    except (requests.RequestException, ValueError) as e:
        raise ErroHospedagem(f"Erro de conexão com o ImgBB: {e}") from e

    if not resposta.ok or not resultado.get("success"):
        mensagem = (resultado.get("error") or {}).get("message", f"HTTP {resposta.status_code}")
        raise ErroHospedagem(f"Falha no upload para o ImgBB: {mensagem}")

    dados = resultado["data"]
    return {
        "public_url": dados["url"],
        "display_url": dados.get("display_url"),
        "delete_url": dados.get("delete_url"),
        "width": dados.get("width"),
        "height": dados.get("height"),
        "size": dados.get("size"),
        "format": "jpg",
    }
