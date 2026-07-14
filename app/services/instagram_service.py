import requests
import time
from typing import Optional
from app.core import config


def publicar_no_feed(
    image_url: str,
    caption: str,
    ig_user_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """
    Publica imagem e legenda no feed do Instagram via Graph API.
    Usa credenciais do usuário logado ou fallback do .env.
    """
    ig_user_id = ig_user_id or config.IG_USER_ID
    access_token = access_token or config.USER_ACCESS_TOKEN

    if not ig_user_id or not access_token:
        return {
            "error": "Conta Instagram não configurada",
            "detail": (
                "Faça login com Instagram (GET /api/auth/instagram/login) "
                "ou configure IG_USER_ID e USER_ACCESS_TOKEN no .env"
            ),
        }

    graph_base = f"https://graph.facebook.com/{config.META_GRAPH_VERSION}"

    container_url = f"{graph_base}/{ig_user_id}/media"
    media_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }
    media_response = requests.post(container_url, data=media_payload, timeout=60)
    media_result = media_response.json()
    if "id" not in media_result:
        return {"error": "Falha ao criar container", "detail": media_result}

    container_id = media_result["id"]
    time.sleep(15)

    publish_url = f"{graph_base}/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    publish_response = requests.post(publish_url, data=publish_payload, timeout=60)
    publish_result = publish_response.json()
    if "id" not in publish_result:
        return {"error": "Falha ao publicar post", "detail": publish_result}

    media_id = publish_result["id"]

    details_url = f"{graph_base}/{media_id}"
    details_params = {
        "fields": "permalink,media_url,caption",
        "access_token": access_token,
    }
    details_response = requests.get(details_url, params=details_params, timeout=30)
    details_result = details_response.json()

    return {
        "permalink": details_result.get("permalink"),
        "media_url": details_result.get("media_url"),
        "caption": details_result.get("caption"),
        "media_id": media_id,
    }
