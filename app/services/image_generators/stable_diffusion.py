"""
Serviço de geração de imagens usando Stable Diffusion (via Replicate ou Hugging Face)
Como alternativa ao Midjourney que não tem API pública oficial
"""
import os
from dotenv import load_dotenv
from app.services.cloud_storage_service import upload_imagem_para_cloud, upload_para_imgbb

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"

def gerar_imagem_stable_diffusion(params):
    """
    Gera uma imagem usando Stable Diffusion via Replicate e faz upload automático para cloud storage.
    
    Args:
        params: Dicionário com parâmetros (tema, público, rede_alvo, formato)
    
    Returns:
        dict: URL pública da imagem, public_id, cloud_info, etc.
    """
    # Importa replicate apenas quando necessário para evitar erro se não estiver instalado
    try:
        import replicate
    except ImportError:
        return {
            'modelo': 'stable-diffusion',
            'status': 'error',
            'error': 'Módulo replicate não instalado. Execute: pip install replicate'
        }
    
    if not REPLICATE_API_TOKEN:
        return {
            'modelo': 'stable-diffusion',
            'status': 'error',
            'error': 'REPLICATE_API_TOKEN não configurada no .env'
        }
    
    # Valida o formato do token
    from app.utils.validators import validar_token_replicate
    token_valido, erro_msg = validar_token_replicate(REPLICATE_API_TOKEN)
    if not token_valido:
        return {
            'modelo': 'stable-diffusion',
            'status': 'error',
            'error': f'REPLICATE_API_TOKEN inválido: {erro_msg}'
        }
    
    # Usa prompt otimizado com metodologia Co-STAR (versão em inglês para Stable Diffusion)
    from app.utils.prompt_engineering import construir_prompt_imagem_simples
    prompt_img = construir_prompt_imagem_simples(params, em_portugues=False)
    
    try:
        # Configura o cliente Replicate
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
        
        # Usa Stable Diffusion XL via Replicate
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt_img,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
        )
        
        # Replicate retorna uma lista de URLs
        if output and len(output) > 0:
            url_imagem_temporaria = output[0] if isinstance(output, list) else output
            
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
                'modelo': 'stable-diffusion',
                'url_temporaria': url_imagem_temporaria,
                'url_publica': url_publica,
                'public_id': public_id,
                'cloud_info': cloud_result,
                'status': 'success'
            }
        else:
            return {
                'modelo': 'stable-diffusion',
                'status': 'error',
                'error': 'Nenhuma imagem gerada pelo Stable Diffusion'
            }
    
    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com Stable Diffusion: {str(e)}")
        return {
            'modelo': 'stable-diffusion',
            'status': 'error',
            'error': str(e)
        }

