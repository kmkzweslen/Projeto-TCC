"""
Publicação no feed do Instagram (Instagram Graph API, login via Facebook).

Fluxo oficial em duas etapas:
  1. POST /{ig-user-id}/media           -> cria o contêiner (image_url + caption)
  2. GET  /{container-id}?fields=status_code até FINISHED
  3. POST /{ig-user-id}/media_publish    -> publica o contêiner

Antes de publicar, consulta-se /{ig-user-id}/content_publishing_limit para
respeitar o limite de publicações via API em 24 horas.
"""
import time
from typing import Callable, Dict, Optional

import requests

from app.core import config

TIMEOUT_HTTP_S = 30
LIMITE_CARACTERES_LEGENDA = 2200
LIMITE_HASHTAGS = 30


class ErroPublicacao(Exception):
    def __init__(self, etapa: str, mensagem: str, detalhes: Optional[Dict] = None):
        super().__init__(mensagem)
        self.etapa = etapa
        self.mensagem = mensagem
        self.detalhes = detalhes or {}


def _url(caminho: str) -> str:
    return f"https://graph.facebook.com/{config.META_GRAPH_VERSION}/{caminho}"


def _erro_graph(dados: Dict) -> str:
    erro = dados.get("error") or {}
    return erro.get("error_user_msg") or erro.get("message") or str(dados)


def validar_publicacao(image_url: str, caption: str) -> None:
    """Valida os dados antes de chamar a API (evita chamadas que falhariam)."""
    if not image_url.lower().startswith("https://"):
        raise ErroPublicacao("validacao", "A imagem precisa estar em uma URL pública HTTPS.")
    if len(caption) > LIMITE_CARACTERES_LEGENDA:
        raise ErroPublicacao(
            "validacao",
            f"A legenda tem {len(caption)} caracteres; o limite do Instagram é {LIMITE_CARACTERES_LEGENDA}.",
        )
    if caption.count("#") > LIMITE_HASHTAGS:
        raise ErroPublicacao("validacao", f"A legenda excede o limite de {LIMITE_HASHTAGS} hashtags.")


def consultar_limite_publicacao(ig_user_id: str, access_token: str) -> Optional[Dict]:
    """Retorna {'usadas': n, 'total': m} ou None se a consulta falhar."""
    try:
        resposta = requests.get(
            _url(f"{ig_user_id}/content_publishing_limit"),
            params={"fields": "config,quota_usage", "access_token": access_token},
            timeout=TIMEOUT_HTTP_S,
        )
        dados = (resposta.json().get("data") or [{}])[0]
        usadas = dados.get("quota_usage")
        total = (dados.get("config") or {}).get("quota_total")
        if usadas is None or total is None:
            return None
        return {"usadas": int(usadas), "total": int(total)}
    except (requests.RequestException, ValueError, TypeError):
        return None


def criar_container(ig_user_id: str, access_token: str, image_url: str, caption: str) -> str:
    resposta = requests.post(
        _url(f"{ig_user_id}/media"),
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
        timeout=TIMEOUT_HTTP_S,
    )
    dados = resposta.json()
    if "id" not in dados:
        raise ErroPublicacao("criar_container", _erro_graph(dados), dados)
    return dados["id"]


def aguardar_container(
    container_id: str,
    access_token: str,
    intervalo_s: Optional[float] = None,
    timeout_s: Optional[float] = None,
    dormir: Callable[[float], None] = time.sleep,
    relogio: Callable[[], float] = time.monotonic,
) -> str:
    """Consulta status_code até FINISHED. Lança ErroPublicacao em ERROR/EXPIRED/tempo esgotado."""
    intervalo_s = config.IG_STATUS_POLL_INTERVAL_S if intervalo_s is None else intervalo_s
    timeout_s = config.IG_STATUS_POLL_TIMEOUT_S if timeout_s is None else timeout_s
    limite = relogio() + timeout_s
    status = None

    while True:
        resposta = requests.get(
            _url(container_id),
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=TIMEOUT_HTTP_S,
        )
        dados = resposta.json()
        status = dados.get("status_code")
        if status in ("FINISHED", "PUBLISHED"):
            return status
        if status in ("ERROR", "EXPIRED"):
            raise ErroPublicacao(
                "processar_container",
                f"Contêiner com status {status}: {dados.get('status') or _erro_graph(dados)}",
                dados,
            )
        if "error" in dados:
            raise ErroPublicacao("processar_container", _erro_graph(dados), dados)
        if relogio() >= limite:
            raise ErroPublicacao(
                "processar_container",
                f"O contêiner não ficou pronto em {timeout_s:.0f} s (último status: {status}).",
            )
        dormir(intervalo_s)


def publicar_container(ig_user_id: str, access_token: str, container_id: str) -> str:
    resposta = requests.post(
        _url(f"{ig_user_id}/media_publish"),
        data={"creation_id": container_id, "access_token": access_token},
        timeout=TIMEOUT_HTTP_S,
    )
    dados = resposta.json()
    if "id" not in dados:
        raise ErroPublicacao("publicar", _erro_graph(dados), dados)
    return dados["id"]


def obter_detalhes_midia(media_id: str, access_token: str) -> Dict:
    try:
        resposta = requests.get(
            _url(media_id),
            params={"fields": "id,permalink,media_url,caption,timestamp", "access_token": access_token},
            timeout=TIMEOUT_HTTP_S,
        )
        return resposta.json()
    except (requests.RequestException, ValueError):
        return {}


def publicar_no_feed(
    image_url: str,
    caption: str,
    ig_user_id: Optional[str] = None,
    access_token: Optional[str] = None,
    dormir: Callable[[float], None] = time.sleep,
) -> Dict:
    """
    Publica uma imagem com legenda no feed.

    Retorna {'media_id', 'permalink', ...} em caso de sucesso ou
    {'error': mensagem, 'etapa': ...} em caso de falha.
    """
    ig_user_id = ig_user_id or config.IG_USER_ID
    access_token = access_token or config.USER_ACCESS_TOKEN
    if not ig_user_id or not access_token:
        return {"error": "Conta do Instagram não vinculada (ig_user_id/access_token ausentes).", "etapa": "validacao"}

    inicio = time.perf_counter()
    try:
        validar_publicacao(image_url, caption)

        limite = consultar_limite_publicacao(ig_user_id, access_token)
        if limite and limite["usadas"] >= limite["total"]:
            raise ErroPublicacao(
                "limite",
                f"Limite de publicações via API atingido ({limite['usadas']}/{limite['total']} em 24 h).",
                limite,
            )

        container_id = criar_container(ig_user_id, access_token, image_url, caption)
        aguardar_container(container_id, access_token, dormir=dormir)
        media_id = publicar_container(ig_user_id, access_token, container_id)
        detalhes = obter_detalhes_midia(media_id, access_token)

        return {
            "media_id": media_id,
            "container_id": container_id,
            "permalink": detalhes.get("permalink"),
            "media_url": detalhes.get("media_url"),
            "caption": detalhes.get("caption", caption),
            "limite_publicacao": limite,
            "tempo_s": round(time.perf_counter() - inicio, 2),
        }
    except ErroPublicacao as e:
        return {
            "error": e.mensagem,
            "etapa": e.etapa,
            "detalhes": e.detalhes,
            "tempo_s": round(time.perf_counter() - inicio, 2),
        }
    except (requests.RequestException, ValueError) as e:
        return {
            "error": f"Erro de comunicação com a Graph API: {e}",
            "etapa": "rede",
            "tempo_s": round(time.perf_counter() - inicio, 2),
        }
