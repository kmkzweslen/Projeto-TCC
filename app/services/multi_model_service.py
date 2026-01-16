"""
Serviço coordenador para gerar conteúdo usando múltiplos modelos em paralelo.
Combina todas as imagens e legendas geradas e retorna todas as opções para o usuário escolher.
"""
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Importar geradores de imagens
from app.services.image_generators.dalle import gerar_imagem_dalle
# from app.services.image_generators.leonardo import gerar_imagem_leonardo  # Desabilitado - serviço pago
from app.services.image_generators.stable_diffusion import gerar_imagem_stable_diffusion
from app.services.image_generators.stability_ai import gerar_imagem_stability_ai
# from app.services.image_generators.gemini import gerar_imagem_gemini  # Desabilitado - não funciona ainda

# Importar geradores de textos
from app.services.text_generators.gpt import gerar_legenda_gpt35, gerar_legenda_gpt4
from app.services.text_generators.claude import gerar_legenda_claude
from app.services.text_generators.gemini import gerar_legenda_gemini

# Importar validadores
from app.utils.validators import verificar_configuracao_modelo

def gerar_todas_imagens(params: Dict) -> List[Dict]:
    """
    Gera imagens usando todos os modelos disponíveis em paralelo.
    
    Args:
        params: Dicionário com parâmetros de entrada
    
    Returns:
        Lista de resultados de geração de imagens
    """
    print("🎨 Iniciando geração de imagens com todos os modelos...")
    
    # Lista de funções de geração de imagens
    # Verifica se as chaves estão configuradas e são válidas antes de adicionar
    geradores_imagens = [
        ("dalle-3", gerar_imagem_dalle),  # Obrigatório - sempre tenta
        # ("leonardo", gerar_imagem_leonardo),  # Desabilitado - serviço pago
    ]
    
    # Adiciona Stable Diffusion (Replicate) apenas se token estiver configurado e válido
    replicate_token, is_valid, error_msg = verificar_configuracao_modelo("REPLICATE_API_TOKEN", validar_formato=True)
    if is_valid:
        geradores_imagens.append(("stable-diffusion", gerar_imagem_stable_diffusion))
    elif replicate_token:
        print(f"⚠️ Stable Diffusion desabilitado: {error_msg}")
    
    # Adiciona Stability AI (API oficial) se a chave estiver configurada e válida
    stability_token1, is_valid1, error_msg1 = verificar_configuracao_modelo("STABILITY_AI_API_KEY", validar_formato=True)
    stability_token2, is_valid2, error_msg2 = verificar_configuracao_modelo("STABILITY_API_KEY", validar_formato=True)
    if is_valid1 or is_valid2:
        geradores_imagens.append(("stability-ai", gerar_imagem_stability_ai))
    elif stability_token1 or stability_token2:
        print(f"⚠️ Stability AI desabilitado: {error_msg1 if stability_token1 else error_msg2}")
    
    # Gemini imagem desabilitado - ainda não funciona
    # geradores_imagens.append(("gemini", gerar_imagem_gemini))
    
    # Executa todos em paralelo usando ThreadPoolExecutor
    resultados = []
    max_workers = min(len(geradores_imagens), 3)  # Ajusta workers baseado no número de modelos
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(gerador, params): nome 
            for nome, gerador in geradores_imagens
        }
        
        for future in futures:
            nome_modelo = futures[future]
            try:
                resultado = future.result(timeout=90)  # Timeout reduzido para 90 segundos por modelo
                resultados.append(resultado)
                if resultado.get('status') == 'success':
                    print(f"✅ {nome_modelo}: Imagem gerada com sucesso")
                else:
                    print(f"❌ {nome_modelo}: {resultado.get('error', 'Erro desconhecido')}")
            except FuturesTimeoutError:
                print(f"⏱️ {nome_modelo}: Timeout após 90 segundos")
                resultados.append({
                    'modelo': nome_modelo,
                    'status': 'error',
                    'error': 'Timeout: Modelo demorou mais de 90 segundos para responder'
                })
            except Exception as e:
                print(f"❌ {nome_modelo}: Exceção - {str(e)}")
                resultados.append({
                    'modelo': nome_modelo,
                    'status': 'error',
                    'error': str(e)
                })
    
    return resultados

def gerar_todas_legendas(params: Dict) -> List[Dict]:
    """
    Gera legendas usando todos os modelos disponíveis em paralelo.
    
    Args:
        params: Dicionário com parâmetros de entrada
    
    Returns:
        Lista de resultados de geração de legendas
    """
    print("📝 Iniciando geração de legendas com todos os modelos...")
    
    # Lista de funções de geração de legendas
    # Verifica se as chaves estão configuradas antes de adicionar
    geradores_legendas = [
        ("gpt-3.5-turbo", gerar_legenda_gpt35),  # Obrigatório - sempre tenta
    ]
    
    # Adiciona GPT-4 se a mesma API key estiver configurada
    openai_key, is_valid, error_msg = verificar_configuracao_modelo("OPENAI_API_KEY", validar_formato=True)
    if is_valid:
        geradores_legendas.append(("gpt-4", gerar_legenda_gpt4))
    
    # Adiciona Claude apenas se API key estiver configurada
    claude_key, is_valid, error_msg = verificar_configuracao_modelo("ANTHROPIC_API_KEY")
    if is_valid:
        geradores_legendas.append(("claude", gerar_legenda_claude))
    
    # Gemini desabilitado temporariamente - está dando timeout
    # gemini_key, is_valid, error_msg = verificar_configuracao_modelo("GEMINI_API_KEY")
    # if is_valid:
    #     geradores_legendas.append(("gemini", gerar_legenda_gemini))
    
    # Executa todos em paralelo usando ThreadPoolExecutor
    resultados = []
    max_workers = min(len(geradores_legendas), 4)  # Ajusta workers baseado no número de modelos
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(gerador, params): nome 
            for nome, gerador in geradores_legendas
        }
        
        for future in futures:
            nome_modelo = futures[future]
            try:
                resultado = future.result(timeout=45)  # Timeout reduzido para 45 segundos por modelo
                resultados.append(resultado)
                if resultado.get('status') == 'success':
                    print(f"✅ {nome_modelo}: Legenda gerada com sucesso")
                else:
                    print(f"❌ {nome_modelo}: {resultado.get('error', 'Erro desconhecido')}")
            except FuturesTimeoutError:
                print(f"⏱️ {nome_modelo}: Timeout após 45 segundos")
                resultados.append({
                    'modelo': nome_modelo,
                    'status': 'error',
                    'error': 'Timeout: Modelo demorou mais de 45 segundos para responder'
                })
            except Exception as e:
                print(f"❌ {nome_modelo}: Exceção - {str(e)}")
                resultados.append({
                    'modelo': nome_modelo,
                    'status': 'error',
                    'error': str(e)
                })
    
    return resultados

def gerar_conteudo_multi_modelo(params: Dict) -> Dict:
    """
    Gera conteúdo completo (imagens + legendas) usando todos os modelos disponíveis.
    Retorna todas as combinações possíveis para o usuário escolher.
    
    Args:
        params: Dicionário com parâmetros de entrada
    
    Returns:
        Dict com todas as opções geradas (imagens e legendas separadas)
    """
    if params.get('tipo', '').lower() != "imagem":
        # Se não for imagem, só gera legendas
        legendas = gerar_todas_legendas(params)
        return {
            "tipo": "texto",
            "legendas": legendas
        }
    
    # Gera imagens e legendas em paralelo
    imagens = gerar_todas_imagens(params)
    legendas = gerar_todas_legendas(params)
    
    # Filtra apenas os resultados com sucesso
    imagens_sucesso = [img for img in imagens if img.get('status') == 'success']
    legendas_sucesso = [leg for leg in legendas if leg.get('status') == 'success']
    
    print(f"\n📊 Resultados:")
    print(f"  ✅ {len(imagens_sucesso)}/{len(imagens)} imagens geradas com sucesso")
    print(f"  ✅ {len(legendas_sucesso)}/{len(legendas)} legendas geradas com sucesso")
    
    return {
        "tipo": "imagem",
        "imagens": imagens_sucesso,
        "legendas": legendas_sucesso,
        "imagens_falhas": [img for img in imagens if img.get('status') != 'success'],
        "legendas_falhas": [leg for leg in legendas if leg.get('status') != 'success'],
        "total_combinacoes": len(imagens_sucesso) * len(legendas_sucesso) if imagens_sucesso and legendas_sucesso else 0
    }

