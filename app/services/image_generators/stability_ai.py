"""
Serviço de geração de imagens usando Stability AI diretamente (não via Replicate)
API oficial: https://platform.stability.ai/
"""
import os
import requests
import base64
from io import BytesIO
from dotenv import load_dotenv
from app.services.cloud_storage_service import upload_imagem_para_cloud, upload_para_imgbb

load_dotenv()

STABILITY_AI_API_KEY = os.getenv("STABILITY_AI_API_KEY") or os.getenv("STABILITY_API_KEY")
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"
STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

def gerar_imagem_stability_ai(params):
    """
    Gera uma imagem usando Stability AI diretamente.
    
    Args:
        params: Dicionário com parâmetros (tema, público, rede_alvo, formato)
    
    Returns:
        dict: URL pública da imagem, public_id, cloud_info, etc.
    """
    if not STABILITY_AI_API_KEY:
        return {
            'modelo': 'stability-ai',
            'status': 'error',
            'error': 'STABILITY_AI_API_KEY ou STABILITY_API_KEY não configurada no .env'
        }
    
    # Valida o formato do token
    from app.utils.validators import validar_token_stability_ai
    token_valido, erro_msg = validar_token_stability_ai(STABILITY_AI_API_KEY)
    if not token_valido:
        return {
            'modelo': 'stability-ai',
            'status': 'error',
            'error': f'Token Stability AI inválido: {erro_msg}'
        }
    
    # ⚠️ IMPORTANTE: Stability AI APENAS ACEITA PROMPTS EM INGLÊS!
    # Usa prompt otimizado com metodologia Co-STAR
    from app.utils.prompt_engineering import construir_prompt_imagem_simples
    prompt_img = construir_prompt_imagem_simples(params, em_portugues=False)
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {STABILITY_AI_API_KEY}"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt_img
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        print("🖼️  Gerando imagem com Stability AI...")
        response = requests.post(
            STABILITY_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            error_msg = response.text
            return {
                'modelo': 'stability-ai',
                'status': 'error',
                'error': f'Erro na API Stability AI ({response.status_code}): {error_msg}'
            }
        
        result = response.json()
        
        # A API retorna a imagem em base64
        if 'artifacts' in result and len(result['artifacts']) > 0:
            image_base64 = result['artifacts'][0].get('base64')
            
            if not image_base64:
                return {
                    'modelo': 'stability-ai',
                    'status': 'error',
                    'error': 'Nenhuma imagem retornada pela API Stability AI'
                }
            
            # Converte base64 para bytes
            image_bytes = base64.b64decode(image_base64)
            
            # Converte para JPG usando PIL
            from PIL import Image
            image = Image.open(BytesIO(image_bytes))
            
            # Converte para RGB se necessário
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Salva como JPG em BytesIO
            jpg_buffer = BytesIO()
            image.save(jpg_buffer, 'JPEG', quality=95, optimize=True)
            jpg_buffer.seek(0)
            
            # Upload para cloud storage
            # Cloudinary aceita BytesIO diretamente
            if USE_CLOUDINARY:
                cloud_result = upload_imagem_para_cloud(jpg_buffer)
                url_publica = cloud_result['secure_url']
                public_id = cloud_result.get('public_id')
            else:
                # Usa função existente que agora aceita BytesIO
                cloud_result = upload_para_imgbb(jpg_buffer)
                url_publica = cloud_result['secure_url']
                public_id = None
            
            return {
                'modelo': 'stability-ai',
                'url_publica': url_publica,
                'public_id': public_id,
                'cloud_info': cloud_result,
                'status': 'success'
            }
        else:
            return {
                'modelo': 'stability-ai',
                'status': 'error',
                'error': 'Resposta da API Stability AI sem imagens'
            }
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro ao gerar imagem com Stability AI: {str(e)}")
        return {
            'modelo': 'stability-ai',
            'status': 'error',
            'error': f'Erro de conexão: {str(e)}'
        }
    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com Stability AI: {str(e)}")
        return {
            'modelo': 'stability-ai',
            'status': 'error',
            'error': str(e)
        }

