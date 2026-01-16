"""
Serviço de geração de imagens usando Gemini/Nano Banana (Google)
Nota: A geração de imagens via Gemini API ainda está em desenvolvimento.
Esta é uma implementação placeholder que pode ser atualizada quando a API estiver disponível.
"""
import os
from dotenv import load_dotenv
from app.services.cloud_storage_service import upload_imagem_para_cloud, upload_para_imgbb

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"

def gerar_imagem_gemini(params):
    if not GEMINI_API_KEY:
        return {
            'modelo': 'gemini',
            'status': 'error',
            'error': 'GEMINI_API_KEY não configurada no .env'
        }
    
    # Por enquanto, retorna erro informativo
    # Quando a API do Gemini para geração de imagens estiver disponível,
    return {
        'modelo': 'gemini',
        'status': 'error',
        'error': 'Geração de imagens via Gemini/Nano Banana ainda não está disponível na API pública. Use DALL-E, Leonardo.ai ou Stable Diffusion.'
    }

