"""
Serviço de geração de legendas usando Gemini (Google) via LangChain
"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def gerar_legenda_gemini(params):
    """
    Gera uma legenda usando Gemini (Google) via LangChain.
    
    Args:
        params: Dicionário com parâmetros (tema, tipo, objetivo, público, tom, rede_alvo, formato)
    
    Returns:
        dict: Legenda gerada e informações do modelo
    """
    # Importa LangChain para Gemini apenas quando necessário
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return {
            'modelo': 'gemini',
            'status': 'error',
            'error': 'Módulo langchain-google-genai não instalado. Execute: pip install langchain-google-genai'
        }
    
    if not GEMINI_API_KEY:
        return {
            'modelo': 'gemini',
            'status': 'error',
            'error': 'GEMINI_API_KEY não configurada no .env'
        }
    
    # Usa metodologia Co-STAR para construção do prompt
    from app.utils.prompt_engineering import construir_prompt_co_star
    prompt = construir_prompt_co_star(params, tipo="legenda")
    
    # Lista modelos para tentar (LangChain pode usar diferentes formatos)
    modelos_para_tentar = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
        'gemini-1.5-flash-latest',
        'gemini-pro-latest'
    ]
    
    try:
        modelo_usado = None
        erro_modelo = None
        
        # Tenta cada modelo até encontrar um que funcione
        for modelo_nome in modelos_para_tentar:
            try:
                llm_gemini = ChatGoogleGenerativeAI(
                    model=modelo_nome,
                    temperature=0.7,
                    max_output_tokens=1024,
                    google_api_key=GEMINI_API_KEY
                )
                
                messages = [
                    ("system", "Você é um especialista em marketing digital e criação de conteúdo para redes sociais. Siga rigorosamente todas as diretrizes fornecidas."),
                    ("human", prompt)
                ]
                
                resposta = llm_gemini.invoke(messages)
                modelo_usado = modelo_nome
                
                return {
                    'modelo': 'gemini',
                    'legenda': resposta.content,
                    'status': 'success'
                }
            except Exception as e:
                erro_msg = str(e)
                erro_modelo = erro_msg
                # Continua tentando outros modelos
                continue
        
        # Se nenhum modelo funcionou
        return {
            'modelo': 'gemini',
            'status': 'error',
            'error': f'Nenhum modelo Gemini disponível. Último erro: {erro_modelo[:150] if erro_modelo else "N/A"}'
        }
                
    except Exception as e:
        print(f"⚠️ Erro ao gerar legenda com Gemini: {str(e)}")
        return {
            'modelo': 'gemini',
            'status': 'error',
            'error': str(e)
        }

