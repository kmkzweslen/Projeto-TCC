"""
Serviço de edição de imagens usando Stability AI (alternativa ao Replicate)
Permite fazer upload de uma imagem e editá-la com base em prompts usando a API oficial da Stability AI
"""
import os
import requests
import base64
from io import BytesIO
from dotenv import load_dotenv
from app.services.cloud_storage_service import upload_imagem_para_cloud, upload_para_imgbb
from app.utils.imagem import baixar_e_converter_para_jpg, validar_imagem
from PIL import Image

load_dotenv()

STABILITY_AI_API_KEY = os.getenv("STABILITY_AI_API_KEY") or os.getenv("STABILITY_API_KEY")
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Para tradução de prompts

# Endpoint da Stability AI para image-to-image
# Usando o endpoint correto para SDXL image-to-image
STABILITY_IMG2IMG_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"


def _traduzir_prompt_para_ingles(prompt: str) -> str:
    """
    Traduz um prompt de português para inglês usando GPT-3.5.
    Se não conseguir traduzir, retorna o prompt original (assumindo que já está em inglês).
    Melhora o prompt para ser mais específico sobre edições de imagem.
    
    Args:
        prompt: Prompt em português ou inglês
    
    Returns:
        Prompt em inglês otimizado para image-to-image
    """
    # Se já parece estar em inglês (contém muitas palavras comuns em inglês), retorna como está
    palavras_ingles_comuns = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    palavras_prompt = prompt.lower().split()
    palavras_ingles_no_prompt = sum(1 for palavra in palavras_prompt if palavra in palavras_ingles_comuns)
    
    # Se mais de 20% das palavras são palavras comuns em inglês, assume que já está em inglês
    if len(palavras_prompt) > 0 and palavras_ingles_no_prompt / len(palavras_prompt) > 0.2:
        return prompt
    
    # Tenta traduzir usando GPT-3.5 se a chave estiver disponível
    if OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, openai_api_key=OPENAI_API_KEY)
            # Prompt melhorado para tradução de edições de imagem
            mensagem = f"""Traduza o seguinte prompt de edição de imagem para inglês, mantendo o significado exato e técnico.
Para mudanças de cor ou objetos, seja muito específico e direto (ex: "change the car color from blue to red" ou "make the car red instead of blue").
Retorne APENAS a tradução em inglês, sem explicações ou comentários adicionais:

{prompt}"""
            resposta = llm.invoke([("human", mensagem)])
            prompt_traduzido = resposta.content.strip()
            
            # Remove aspas se o modelo adicionou
            if prompt_traduzido.startswith('"') and prompt_traduzido.endswith('"'):
                prompt_traduzido = prompt_traduzido[1:-1]
            if prompt_traduzido.startswith("'") and prompt_traduzido.endswith("'"):
                prompt_traduzido = prompt_traduzido[1:-1]
            
            return prompt_traduzido
        except Exception as e:
            print(f"⚠️ Erro ao traduzir prompt: {str(e)}. Usando prompt original.")
            return prompt
    
    # Se não conseguir traduzir, retorna o prompt original
    return prompt

def editar_imagem_com_prompt_stability(image_url_or_file, prompt: str, strength: float = 0.7, num_outputs: int = 1):
    """
    Edita uma imagem existente usando Stability AI image-to-image.
    
    Args:
        image_url_or_file: URL da imagem ou arquivo uploadado (UploadFile do FastAPI)
        prompt: Prompt descrevendo as alterações desejadas (em inglês)
        strength: Força da edição (0.0-1.0). 0.0 mantém original, 1.0 transforma completamente
        num_outputs: Número de variações a gerar (1-4)
    
    Returns:
        dict: URLs públicas das imagens editadas, public_id, cloud_info, etc.
    """
    if not STABILITY_AI_API_KEY:
        return {
            'status': 'error',
            'error': 'STABILITY_AI_API_KEY ou STABILITY_API_KEY não configurada no .env'
        }
    
    # Valida o formato do token
    from app.utils.validators import validar_token_stability_ai
    token_valido, erro_msg = validar_token_stability_ai(STABILITY_AI_API_KEY)
    if not token_valido:
        return {
            'status': 'error',
            'error': f'Token Stability AI inválido: {erro_msg}'
        }
    
    try:
        # Processa a imagem de entrada
        if hasattr(image_url_or_file, 'read'):
            # É um UploadFile do FastAPI
            image_data = image_url_or_file.file.read()
            image_buffer = BytesIO(image_data)
        elif isinstance(image_url_or_file, str) and image_url_or_file.startswith('http'):
            # É uma URL
            info = validar_imagem(image_url_or_file)
            if not info['valida']:
                return {
                    'status': 'error',
                    'error': f"Imagem inválida: {info.get('erro')}"
                }
            
            # Baixa e converte para formato compatível
            image_buffer = baixar_e_converter_para_jpg(image_url_or_file)
            # Garante que o buffer está no início
            if hasattr(image_buffer, 'seek'):
                image_buffer.seek(0)
        else:
            return {
                'status': 'error',
                'error': 'Formato de imagem não suportado. Use URL ou upload de arquivo.'
            }
        
        # Prepara a imagem para a API
        # Garante que o buffer está no início antes de abrir
        if hasattr(image_buffer, 'seek'):
            image_buffer.seek(0)
        
        # Verifica se o buffer tem conteúdo
        if hasattr(image_buffer, 'tell') and hasattr(image_buffer, 'read'):
            pos_atual = image_buffer.tell()
            image_buffer.seek(0, 2)  # Vai para o final
            tamanho = image_buffer.tell()
            image_buffer.seek(0)  # Volta para o início
            
            print(f"📊 Tamanho do buffer: {tamanho} bytes")
            
            if tamanho == 0:
                return {
                    'status': 'error',
                    'error': 'Imagem baixada está vazia ou corrompida'
                }
        
        # Tenta abrir a imagem
        try:
            image = Image.open(image_buffer)
        except Exception as img_error:
            print(f"⚠️ Erro ao abrir imagem: {str(img_error)}")
            print(f"📋 Tipo do buffer: {type(image_buffer)}")
            if hasattr(image_buffer, 'tell'):
                print(f"📋 Posição do buffer: {image_buffer.tell()}")
            raise
        
        print(f"📷 Imagem original: {image.size} ({image.width}x{image.height}), modo: {image.mode}")
        
        # Converte para RGB se necessário
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Redimensiona para uma das dimensões permitidas pela Stability AI
        # Dimensões permitidas: 1024x1024, 1152x896, 1216x832, 1344x768, 1536x640, 
        # 640x1536, 768x1344, 832x1216, 896x1152
        allowed_dimensions = [
            (1024, 1024), (1152, 896), (1216, 832), (1344, 768), (1536, 640),
            (640, 1536), (768, 1344), (832, 1216), (896, 1152)
        ]
        
        # Encontra a dimensão permitida mais próxima mantendo a proporção
        original_width, original_height = image.size
        original_ratio = original_width / original_height
        best_dim = None
        best_diff = float('inf')
        
        for w, h in allowed_dimensions:
            ratio = w / h
            diff = abs(ratio - original_ratio)
            if diff < best_diff:
                best_diff = diff
                best_dim = (w, h)
        
        # Redimensiona para a dimensão escolhida
        target_width, target_height = best_dim
        if original_width != target_width or original_height != target_height:
            # Usa LANCZOS para melhor qualidade
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            print(f"📐 Imagem redimensionada de {original_width}x{original_height} para {target_width}x{target_height}")
        
        # Verifica se a imagem tem uma das dimensões permitidas (garantia extra)
        current_size = (image.width, image.height)
        if current_size not in allowed_dimensions:
            # Se ainda não estiver nas dimensões permitidas, força para 1024x1024
            print(f"⚠️ Aviso: Dimensão {current_size} não está nas permitidas. Forçando 1024x1024")
            image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        # Converte para base64
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        # Prepara requisição para a API
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {STABILITY_AI_API_KEY}"
        }
        
        # ⚠️ IMPORTANTE: Stability AI APENAS ACEITA PROMPTS EM INGLÊS!
        # Traduz o prompt para inglês se necessário
        prompt_ingles = _traduzir_prompt_para_ingles(prompt)
        print(f"🌐 Prompt original (PT): {prompt}")
        print(f"🌐 Prompt traduzido (EN): {prompt_ingles}")
        
        # A Stability AI image-to-image aceita múltiplas variações
        # Vamos fazer requisições separadas para cada variação
        resultados = []
        
        for i in range(num_outputs):
            # A Stability AI image-to-image requer a imagem como arquivo multipart
            # Vamos converter o base64 de volta para bytes e enviar como arquivo
            image_bytes_for_upload = base64.b64decode(image_base64)
            print(f"📤 Enviando imagem original para edição: {len(image_bytes_for_upload)} bytes")
            
            # Cria um novo BytesIO para cada requisição (importante para multipart)
            image_file_buffer = BytesIO(image_bytes_for_upload)
            image_file_buffer.seek(0)
            
            files = {
                'init_image': ('image.png', image_file_buffer, 'image/png')
            }
            
            # Para mudanças significativas (como trocar cor), precisa de strength muito alto
            # image_strength: 0.0 mantém original, 1.0 transforma completamente
            # Para mudanças de cor/objetos, precisamos de valores MUITO altos (0.9-1.0)
            effective_strength = strength
            
            # Detecta se é mudança de cor e força strength alto
            is_color_change = any(word in prompt_ingles.lower() for word in ['color', 'colour', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'black', 'white', 'trocar', 'mudar', 'change color'])
            
            if is_color_change:
                # Para mudanças de cor, força strength mínimo de 0.9
                effective_strength = max(strength, 0.9)
                if strength < 0.9:
                    print(f"🎨 Mudança de cor detectada! Ajustando strength de {strength} para {effective_strength}")
            elif strength < 0.6:
                # Para outras mudanças, ajusta se muito baixo
                effective_strength = 0.8
                print(f"⚠️ Strength {strength} muito baixo para mudanças significativas. Ajustando para {effective_strength}")
            
            # Melhora o prompt para mudanças de cor - adiciona instruções mais específicas e diretas
            prompt_enhanced = prompt_ingles
            if is_color_change:
                # Para mudanças de cor, torna o prompt muito mais explícito e direto
                if 'change' not in prompt_ingles.lower() and 'make' not in prompt_ingles.lower() and 'turn' not in prompt_ingles.lower():
                    # Adiciona instrução muito mais direta e enfática
                    prompt_enhanced = f"change the color to {prompt_ingles.lower()}, completely replace the original color, make it very obvious and distinct"
                else:
                    # Reforça a instrução existente
                    prompt_enhanced = f"{prompt_ingles}, completely replace the original color, make the change very obvious and distinct"
                print(f"🎨 Prompt melhorado para mudança de cor: {prompt_enhanced}")
            
            # Para mudanças de cor, aumenta ainda mais o cfg_scale
            # Nota: Stability AI limita steps a no máximo 50
            cfg_scale = 9.0 if is_color_change else 8.0
            num_steps = 50  # Máximo permitido pela API
            
            data = {
                'text_prompts[0][text]': prompt_enhanced,  # Usa prompt melhorado
                'cfg_scale': cfg_scale,  # Aumentado para melhor aderência ao prompt
                'image_strength': effective_strength,  # Controla quanto da imagem original manter (0.0-1.0)
                'samples': 1,
                'steps': num_steps,  # Aumentado para melhor qualidade e mais transformação
            }
            
            print(f"📊 Parâmetros: strength={effective_strength}, cfg_scale={cfg_scale}, steps={num_steps}")
            print(f"📝 Prompt final: {prompt_enhanced}")
            
            print(f"🖼️  Editando imagem {i+1}/{num_outputs} com Stability AI...")
            
            # A API da Stability AI para image-to-image usa multipart/form-data
            response = requests.post(
                STABILITY_IMG2IMG_URL,
                headers={"Authorization": f"Bearer {STABILITY_AI_API_KEY}"},  # Remove Accept header para multipart
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = response.text
                print(f"⚠️ Erro na requisição {i+1}: {error_msg}")
                print(f"📋 Status code: {response.status_code}")
                
                # Tenta extrair mensagem de erro mais clara
                try:
                    error_json = response.json()
                    if 'message' in error_json:
                        error_detail = error_json['message']
                        print(f"❌ Erro detalhado: {error_detail}")
                except:
                    pass
                
                # Não continua se houver erro - retorna erro imediatamente
                return {
                    'status': 'error',
                    'error': f'Erro na API Stability AI (status {response.status_code}): {error_msg[:200]}'
                }
            
            result = response.json()
            print(f"✅ Resposta recebida da API. Keys: {result.keys() if isinstance(result, dict) else 'Não é dict'}")
            
            # A API retorna a imagem em base64
            if 'artifacts' in result and len(result['artifacts']) > 0:
                print(f"📦 Artifacts encontrados: {len(result['artifacts'])}")
                artifact = result['artifacts'][0]
                image_base64_result = artifact.get('base64')
                
                # Log do artifact completo para debug
                print(f"📋 Artifact info: finishReason={artifact.get('finishReason')}, seed={artifact.get('seed')}")
                
                if image_base64_result:
                    print(f"✅ Imagem EDITADA base64 recebida (tamanho: {len(image_base64_result)} caracteres)")
                    print(f"🔄 Processando imagem EDITADA retornada pela API...")
                    # Converte base64 para bytes
                    try:
                        image_bytes = base64.b64decode(image_base64_result)
                        print(f"📊 Bytes decodificados: {len(image_bytes)} bytes")
                    except Exception as decode_error:
                        print(f"⚠️ Erro ao decodificar base64: {str(decode_error)}")
                        continue
                    
                    # Abre a imagem
                    try:
                        image_result = Image.open(BytesIO(image_bytes))
                        print(f"🖼️ Imagem editada aberta: {image_result.size} ({image_result.width}x{image_result.height}), modo: {image_result.mode}")
                    except Exception as img_error:
                        print(f"⚠️ Erro ao abrir imagem editada: {str(img_error)}")
                        continue
                    
                    # Converte para RGB se necessário
                    if image_result.mode in ('RGBA', 'LA', 'P'):
                        rgb_image = Image.new('RGB', image_result.size, (255, 255, 255))
                        rgb_image.paste(image_result, mask=image_result.split()[-1] if image_result.mode == 'RGBA' else None)
                        image_result = rgb_image
                    elif image_result.mode != 'RGB':
                        image_result = image_result.convert('RGB')
                    
                    # Salva como JPG em BytesIO
                    jpg_buffer = BytesIO()
                    image_result.save(jpg_buffer, 'JPEG', quality=95, optimize=True)
                    jpg_buffer.seek(0)
                    jpg_size = len(jpg_buffer.getvalue())
                    print(f"💾 Imagem salva como JPG: {jpg_size} bytes")
                    
                    # Verifica se a imagem tem conteúdo válido
                    if jpg_size < 1000:  # Menos de 1KB provavelmente está corrompida
                        print(f"⚠️ Aviso: Imagem muito pequena ({jpg_size} bytes), pode estar corrompida")
                        continue
                    
                    # Upload para cloud storage
                    try:
                        if USE_CLOUDINARY:
                            cloud_result = upload_imagem_para_cloud(jpg_buffer)
                            url_publica = cloud_result['secure_url']
                            public_id = cloud_result.get('public_id')
                        else:
                            # Garante que o buffer está no início antes do upload
                            jpg_buffer.seek(0)
                            cloud_result = upload_para_imgbb(jpg_buffer)
                            url_publica = cloud_result['secure_url']
                            public_id = None
                            print(f"✅ Upload concluído! URL: {url_publica}")
                    except Exception as upload_error:
                        print(f"⚠️ Erro no upload: {str(upload_error)}")
                        continue
                    
                    resultados.append({
                        'url_publica': url_publica,
                        'public_id': public_id,
                        'cloud_info': cloud_result
                    })
                else:
                    print(f"⚠️ Artifact {i+1} não contém base64")
        
        if resultados:
            return {
                'status': 'success',
                'imagens_editadas': resultados,
                'prompt_usado': prompt,
                'strength': strength,
                'modelo': 'stability-ai'
            }
        else:
            return {
                'status': 'error',
                'error': 'Nenhuma imagem editada foi gerada pela Stability AI'
            }
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro ao editar imagem com Stability AI: {str(e)}")
        return {
            'status': 'error',
            'error': f'Erro de conexão com Stability AI: {str(e)}'
        }
    except Exception as e:
        print(f"⚠️ Erro ao editar imagem: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }
