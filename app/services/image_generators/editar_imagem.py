"""
Serviço de edição de imagens usando DALL-E 3 + GPT-4 Vision
Permite fazer upload de uma imagem e editá-la com base em prompts
"""
import os
from dotenv import load_dotenv

load_dotenv()


def editar_imagem_com_prompt(image_url_or_file, prompt: str, strength: float = 0.9, num_outputs: int = 1):
    """
    Edita uma imagem existente usando DALL-E 3 + GPT-4 Vision.
    
    Processo:
    1. Usa GPT-4 Vision para descrever a imagem original em detalhes
    2. Cria um prompt para DALL-E com a descrição + edição solicitada
    3. Gera nova imagem editada com DALL-E
    4. Faz upload para cloud storage
    
    Args:
        image_url_or_file: URL da imagem ou arquivo uploadado (UploadFile do FastAPI)
        prompt: Prompt descrevendo as alterações desejadas
        strength: Não usado neste método (mantido para compatibilidade)
        num_outputs: Número de variações a gerar (1-4)
    
    Returns:
        dict: URLs públicas das imagens editadas, public_id, cloud_info, etc.
    """
    # Usa DALL-E + GPT-4 Vision para edição
    try:
        from app.services.image_generators.editar_imagem_dalle import editar_imagem_com_dalle
        return editar_imagem_com_dalle(image_url_or_file, prompt, strength, num_outputs)
    except Exception as e:
        print(f"⚠️ Erro ao editar imagem com DALL-E: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': f'Erro ao editar imagem: {str(e)}. Verifique se OPENAI_API_KEY está configurada.'
        }
