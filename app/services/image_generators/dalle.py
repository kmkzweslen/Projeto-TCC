"""
Serviço de geração de imagens usando DALL-E 3 (OpenAI)

NOTA: Para geração de imagens DALL-E, é necessário usar o cliente OpenAI diretamente,
pois o LangChain não oferece suporte direto para geração de imagens.
O LangChain é usado para todas as operações de texto/LLM no projeto.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from app.services.cloud_storage_service import upload_para_imgbb

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

def gerar_imagem_dalle(params):
    """
    Gera uma imagem usando DALL-E 3 e faz upload automático para cloud storage.
    
    Args:
        params: Dicionário com parâmetros (tema, público, rede_alvo, formato)
    
    Returns:
        dict: URL pública da imagem, public_id, cloud_info, etc.
    """
    if not openai_api_key:
        return {
            'modelo': 'dalle-3',
            'status': 'error',
            'error': 'OPENAI_API_KEY não configurada no .env'
        }
    
    # Usa prompt otimizado com metodologia Co-STAR
    from app.utils.prompt_engineering import construir_prompt_imagem_simples
    prompt_img = construir_prompt_imagem_simples(params, em_portugues=True)
    
    try:
        # Cria cliente apenas se a chave existir
        client = OpenAI(api_key=openai_api_key)
        
        # Gera a imagem com DALL-E 3
        response = client.images.generate(
            prompt=prompt_img, 
            model="dall-e-3",
            size="1024x1024",
            n=1,
        )
        url_imagem_temporaria = response.data[0].url
        
        # Upload para storage público (projeto simplificado: apenas ImgBB)
        cloud_result = upload_para_imgbb(url_imagem_temporaria)
        url_publica = cloud_result['secure_url']
        public_id = None
        
        return {
            'modelo': 'dalle-3',
            'url_temporaria': url_imagem_temporaria,
            'url_publica': url_publica,
            'public_id': public_id,
            'cloud_info': cloud_result,
            'status': 'success'
        }
    
    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com DALL-E: {str(e)}")
        return {
            'modelo': 'dalle-3',
            'status': 'error',
            'error': str(e)
        }

