"""
Serviço de edição de imagens usando DALL-E 3 (alternativa mais eficaz)
Usa GPT-4 Vision para descrever a imagem original e DALL-E para gerar nova versão editada
Mais eficaz para mudanças drásticas que image-to-image não consegue fazer
"""
import os
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from app.services.cloud_storage_service import upload_imagem_para_cloud, upload_para_imgbb
from app.utils.imagem import baixar_e_converter_para_jpg, validar_imagem
from PIL import Image

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"


def _descrever_imagem_com_gpt_vision(image_url_or_file, prompt_edicao: str):
    """
    Usa GPT-4 Vision para descrever a imagem original e criar um prompt para DALL-E.
    
    Args:
        image_url_or_file: URL da imagem ou arquivo uploadado
        prompt_edicao: Prompt descrevendo a edição desejada
    
    Returns:
        str: Prompt otimizado para DALL-E gerar a imagem editada
    """
    if not OPENAI_API_KEY:
        return None
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Prepara a imagem para o GPT-4 Vision
        if hasattr(image_url_or_file, 'read'):
            # É um UploadFile
            image_data = image_url_or_file.file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        elif isinstance(image_url_or_file, str) and image_url_or_file.startswith('http'):
            # É uma URL - baixa e converte
            response = requests.get(image_url_or_file)
            response.raise_for_status()
            image_base64 = base64.b64encode(response.content).decode('utf-8')
        else:
            return None
        
        # Chama GPT-4 Vision para descrever a imagem e criar prompt para edição
        response = client.chat.completions.create(
            model="gpt-4o",  # GPT-4 Vision
            messages=[
                {
                    "role": "system",
                    "content": "You are an image description expert. Analyze the image and create a detailed prompt in English for DALL-E 3 to generate an edited version."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this image and create a detailed prompt in English for DALL-E 3 to generate a similar image with this modification: {prompt_edicao}

Describe the main visual elements (objects, colors, composition, style, lighting, background) and apply the requested modification.

Return ONLY the prompt in English, no additional explanations."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        prompt_dalle = response.choices[0].message.content.strip()
        return prompt_dalle
        
    except Exception as e:
        print(f"⚠️ Erro ao descrever imagem com GPT-4 Vision: {str(e)}")
        return None


def editar_imagem_com_dalle(image_url_or_file, prompt: str, strength: float = 0.9, num_outputs: int = 1):
    """
    Edita uma imagem usando DALL-E 3 (método alternativo mais eficaz).
    
    Processo:
    1. Usa GPT-4 Vision para descrever a imagem original
    2. Cria um prompt para DALL-E com a descrição + edição
    3. Gera nova imagem com DALL-E
    4. Faz upload para cloud storage
    
    Args:
        image_url_or_file: URL da imagem ou arquivo uploadado (UploadFile do FastAPI)
        prompt: Prompt descrevendo as alterações desejadas
        strength: Não usado neste método (mantido para compatibilidade)
        num_outputs: Número de variações a gerar (1-4)
    
    Returns:
        dict: URLs públicas das imagens editadas, public_id, cloud_info, etc.
    """
    if not OPENAI_API_KEY:
        return {
            'status': 'error',
            'error': 'OPENAI_API_KEY não configurada no .env'
        }
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Passo 1: Descrever imagem com GPT-4 Vision e criar prompt para DALL-E
        print("🔍 Analisando imagem com GPT-4 Vision...")
        prompt_dalle = _descrever_imagem_com_gpt_vision(image_url_or_file, prompt)
        
        if not prompt_dalle:
            # Fallback: cria prompt simples
            print("⚠️ Não foi possível usar GPT-4 Vision. Usando prompt simples...")
            # Traduz o prompt para inglês se necessário
            try:
                from app.services.image_generators.editar_imagem_stability import _traduzir_prompt_para_ingles
                prompt_ingles = _traduzir_prompt_para_ingles(prompt)
            except:
                prompt_ingles = prompt
            
            prompt_dalle = f"An image similar to the original, but with the following modification: {prompt_ingles}. Maintain the general style and composition of the original image."
        
        print(f"📝 Prompt para DALL-E: {prompt_dalle[:200]}...")
        
        # Passo 2: Gerar nova imagem com DALL-E
        resultados = []
        for i in range(num_outputs):
            print(f"🎨 Gerando imagem editada {i+1}/{num_outputs} com DALL-E 3...")
            
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt_dalle,
                    size="1024x1024",
                    n=1,
                    quality="standard"
                )
                
                url_imagem_editada = response.data[0].url
                print(f"✅ Imagem editada gerada: {url_imagem_editada[:50]}...")
                
                # Passo 3: Upload para cloud storage
                if USE_CLOUDINARY:
                    cloud_result = upload_imagem_para_cloud(url_imagem_editada)
                    url_publica = cloud_result['secure_url']
                    public_id = cloud_result.get('public_id')
                else:
                    cloud_result = upload_para_imgbb(url_imagem_editada)
                    url_publica = cloud_result['secure_url']
                    public_id = None
                
                resultados.append({
                    'url_publica': url_publica,
                    'public_id': public_id,
                    'cloud_info': cloud_result
                })
                
            except Exception as e:
                print(f"⚠️ Erro ao gerar imagem {i+1}: {str(e)}")
                continue
        
        if resultados:
            return {
                'status': 'success',
                'imagens_editadas': resultados,
                'prompt_usado': prompt,
                'strength': strength,
                'modelo': 'dalle-3-vision'
            }
        else:
            return {
                'status': 'error',
                'error': 'Nenhuma imagem editada foi gerada pelo DALL-E'
            }
    
    except Exception as e:
        print(f"⚠️ Erro ao editar imagem com DALL-E: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': f'Erro ao editar imagem: {str(e)}'
        }
