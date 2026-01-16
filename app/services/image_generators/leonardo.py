"""
Serviço de geração de imagens usando Leonardo.ai
"""
import os
import requests
import time
from app.services.cloud_storage_service import upload_imagem_para_cloud, upload_para_imgbb

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"
LEONARDO_API_BASE = "https://cloud.leonardo.ai/api/rest/v1"

def gerar_imagem_leonardo(params):
    """
    Gera uma imagem usando Leonardo.ai e faz upload automático para cloud storage.
    
    Args:
        params: Dicionário com parâmetros (tema, público, rede_alvo, formato)
    
    Returns:
        dict: URL pública da imagem, public_id, cloud_info, etc.
    """
    if not LEONARDO_API_KEY:
        return {
            'modelo': 'leonardo',
            'status': 'error',
            'error': 'LEONARDO_API_KEY não configurada no .env'
        }
    
    prompt_img = (
        f"Foto ou ilustração para o tema '{params['tema']}' destinada ao público '{params['publico']}' "
        f"para uso em '{params['rede_alvo']}', formato '{params['formato']}'."
    )
    
    try:
        headers = {
            "Authorization": f"Bearer {LEONARDO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Cria uma geração de imagem usando a API do Leonardo.ai
        payload = {
            "prompt": prompt_img,
            "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Kino XL
            "width": 1024,
            "height": 1024,
            "num_images": 1,
            "guidance_scale": 7
        }
        
        response = requests.post(
            f"{LEONARDO_API_BASE}/generations",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        generation_data = response.json()
        
        generation_id = generation_data.get('sdGenerationJob', {}).get('generationId')
        if not generation_id:
            return {
                'modelo': 'leonardo',
                'status': 'error',
                'error': 'Falha ao criar geração no Leonardo.ai: ' + str(generation_data)
            }
        
        # Aguarda a geração estar pronta (polling)
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            
            get_response = requests.get(
                f"{LEONARDO_API_BASE}/generations/{generation_id}",
                headers=headers
            )
            get_response.raise_for_status()
            result = get_response.json()
            
            generation = result.get('generations_by_pk', {})
            status = generation.get('status')
            
            if status == 'COMPLETE':
                images = generation.get('generated_images', [])
                if images and len(images) > 0:
                    url_imagem_temporaria = images[0].get('url')
                    
                    if url_imagem_temporaria:
                        # Upload para cloud storage
                        if USE_CLOUDINARY:
                            cloud_result = upload_imagem_para_cloud(url_imagem_temporaria)
                            url_publica = cloud_result['secure_url']
                            public_id = cloud_result.get('public_id')
                        else:
                            cloud_result = upload_para_imgbb(url_imagem_temporaria)
                            url_publica = cloud_result['secure_url']
                            public_id = None
                        
                        return {
                            'modelo': 'leonardo',
                            'url_temporaria': url_imagem_temporaria,
                            'url_publica': url_publica,
                            'public_id': public_id,
                            'cloud_info': cloud_result,
                            'status': 'success'
                        }
            
            if status == 'FAILED':
                return {
                    'modelo': 'leonardo',
                    'status': 'error',
                    'error': 'Geração falhou no Leonardo.ai'
                }
        
        return {
            'modelo': 'leonardo',
            'status': 'error',
            'error': 'Timeout aguardando geração do Leonardo.ai'
        }
    
    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com Leonardo.ai: {str(e)}")
        return {
            'modelo': 'leonardo',
            'status': 'error',
            'error': str(e)
        }

