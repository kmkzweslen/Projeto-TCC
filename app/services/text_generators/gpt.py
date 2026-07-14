"""
Serviço de geração de legendas usando GPT (OpenAI)
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

# LLMs serão criados dentro das funções se a chave existir

def gerar_legenda_gpt35(params):
    """
    Gera uma legenda usando GPT-3.5-turbo.
    
    Args:
        params: Dicionário com parâmetros (tema, tipo, objetivo, público, tom, rede_alvo, formato)
    
    Returns:
        dict: Legenda gerada e informações do modelo
    """
    if not openai_api_key:
        return {
            'modelo': 'gpt-3.5-turbo',
            'status': 'error',
            'error': 'OPENAI_API_KEY não configurada no .env'
        }
    
    # Usa metodologia Co-STAR para construção do prompt
    from app.utils.prompt_engineering import construir_prompt_co_star
    prompt = construir_prompt_co_star(params, tipo="legenda")
    
    try:
        llm_gpt35 = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=openai_api_key)
        messages = [
            ("system", "Você é um especialista em marketing digital e criação de conteúdo para redes sociais. Siga rigorosamente todas as diretrizes fornecidas."),
            ("human", prompt)
        ]
        resposta = llm_gpt35.invoke(messages)
        
        return {
            'modelo': 'gpt-3.5-turbo',
            'legenda': resposta.content,
            'status': 'success'
        }
    except Exception as e:
        print(f"⚠️ Erro ao gerar legenda com GPT-3.5: {str(e)}")
        return {
            'modelo': 'gpt-3.5-turbo',
            'status': 'error',
            'error': str(e)
        }

