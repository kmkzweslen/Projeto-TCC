import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

def publicar_no_feed(image_url, caption):
    """
    Publica uma imagem e legenda no feed do Instagram.
    """
    ig_user_id = os.getenv('IG_USER_ID')
    access_token = os.getenv('USER_ACCESS_TOKEN')
    
    if not ig_user_id or not access_token:
        return {
            "error": "Configuração do Instagram incompleta",
            "detail": "IG_USER_ID e USER_ACCESS_TOKEN devem estar configurados no .env"
        }
    container_url = f'https://graph.facebook.com/v17.0/{ig_user_id}/media'
    media_payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }
    media_response = requests.post(container_url, data=media_payload)
    media_result = media_response.json()
    if 'id' not in media_result:
        return {"error": "Falha ao criar container", "detail": media_result}

    container_id = media_result['id']

    time.sleep(15)  # Ajuste para 10-30 s se necessário

    # Publica o post
    publish_url = f'https://graph.facebook.com/v17.0/{ig_user_id}/media_publish'
    publish_payload = {
        'creation_id': container_id,
        'access_token': access_token
    }
    publish_response = requests.post(publish_url, data=publish_payload)
    publish_result = publish_response.json()
    if 'id' not in publish_result:
        return {"error": "Falha ao publicar post", "detail": publish_result}
    media_id = publish_result['id']

    # detalhes/finalização
    details_url = f'https://graph.facebook.com/v17.0/{media_id}'
    details_params = {
        'fields': 'permalink,media_url,caption',
        'access_token': access_token
    }
    details_response = requests.get(details_url, params=details_params)
    details_result = details_response.json()

    return {
        "permalink": details_result.get("permalink"),
        "media_url": details_result.get("media_url"),
        "caption": details_result.get("caption"),
        "media_id": media_id
    }
