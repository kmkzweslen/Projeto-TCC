"""Orquestra geração de imagens e legendas em paralelo."""
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

from app.services.image_generators.dalle import gerar_imagem_dalle
from app.services.image_generators.stability_ai import gerar_imagem_stability_ai

from app.services.text_generators.gpt import gerar_legenda_gpt35
from app.services.text_generators.gemini import gerar_legenda_gemini

from app.utils.validators import verificar_configuracao_modelo

def gerar_todas_imagens(params: Dict) -> List[Dict]:
    """Gera imagens com DALL‑E e (opcionalmente) Stability."""
    print("🎨 Gerando imagens...")
    
    geradores_imagens = [
        ("dalle-3", gerar_imagem_dalle),
    ]
    
    stability_token1, is_valid1, error_msg1 = verificar_configuracao_modelo("STABILITY_AI_API_KEY", validar_formato=True)
    stability_token2, is_valid2, error_msg2 = verificar_configuracao_modelo("STABILITY_API_KEY", validar_formato=True)
    if is_valid1 or is_valid2:
        geradores_imagens.append(("stability-ai", gerar_imagem_stability_ai))
    elif stability_token1 or stability_token2:
        print(f"⚠️ Stability AI desabilitado: {error_msg1 if stability_token1 else error_msg2}")
    
    resultados = []
    max_workers = min(len(geradores_imagens), 3)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(gerador, params): nome 
            for nome, gerador in geradores_imagens
        }
        
        for future in futures:
            nome_modelo = futures[future]
            try:
                resultado = future.result(timeout=90)
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
    """Gera legendas com GPT e (opcionalmente) Gemini."""
    print("📝 Gerando legendas...")
    
    geradores_legendas = [
        ("gpt-3.5-turbo", gerar_legenda_gpt35),
    ]
    
    gemini_key, is_valid, error_msg = verificar_configuracao_modelo("GEMINI_API_KEY")
    if is_valid:
        geradores_legendas.append(("gemini", gerar_legenda_gemini))
    
    resultados = []
    max_workers = min(len(geradores_legendas), 4)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(gerador, params): nome 
            for nome, gerador in geradores_legendas
        }
        
        for future in futures:
            nome_modelo = futures[future]
            try:
                resultado = future.result(timeout=45)
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
    if params.get('tipo', '').lower() != "imagem":
        legendas = gerar_todas_legendas(params)
        return {
            "tipo": "texto",
            "legendas": legendas
        }
    
    imagens = gerar_todas_imagens(params)
    legendas = gerar_todas_legendas(params)
    
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

