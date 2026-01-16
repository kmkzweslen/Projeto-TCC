"""
Serviço de geração de legendas usando Claude (Anthropic) via LangChain
"""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def gerar_legenda_claude(params):
    """
    Gera uma legenda usando Claude (Anthropic) via LangChain.
    
    Args:
        params: Dicionário com parâmetros (tema, tipo, objetivo, público, tom, rede_alvo, formato)
    
    Returns:
        dict: Legenda gerada e informações do modelo
    """
    # Importa LangChain para Claude apenas quando necessário
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        return {
            'modelo': 'claude',
            'status': 'error',
            'error': 'Módulo langchain-anthropic não instalado. Execute: pip install langchain-anthropic'
        }
    
    if not ANTHROPIC_API_KEY:
        return {
            'modelo': 'claude',
            'status': 'error',
            'error': 'ANTHROPIC_API_KEY não configurada no .env'
        }
    
    # Usa metodologia Co-STAR para construção do prompt
    from app.utils.prompt_engineering import construir_prompt_co_star
    prompt = construir_prompt_co_star(params, tipo="legenda")
    
    try:
        llm_claude = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.7,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
        
        messages = [
            ("system", "Você é um especialista em marketing digital e criação de conteúdo para redes sociais. Siga rigorosamente todas as diretrizes fornecidas."),
            ("human", prompt)
        ]
        
        resposta = llm_claude.invoke(messages)
        
        return {
            'modelo': 'claude',
            'legenda': resposta.content,
            'status': 'success'
        }
    except Exception as e:
        error_str = str(e)
        print(f"⚠️ Erro ao gerar legenda com Claude: {error_str}")
        
        # Melhora mensagem de erro para créditos insuficientes
        if 'credit' in error_str.lower() or 'balance' in error_str.lower():
            error_msg = "Créditos insuficientes na conta Anthropic. Por favor, recarregue créditos em https://console.anthropic.com/"
        else:
            error_msg = error_str
        
        return {
            'modelo': 'claude',
            'status': 'error',
            'error': error_msg
        }

