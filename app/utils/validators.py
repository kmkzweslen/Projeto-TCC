"""
Utilitários para validação de tokens e configurações de API
"""
import os
from typing import Optional, Tuple

def validar_token_stability_ai(token: Optional[str]) -> Tuple[bool, str]:
    """
    Valida se o token da Stability AI está no formato correto.
    
    Args:
        token: Token a ser validado
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not token:
        return False, "Token não configurado"
    
    token = token.strip()
    
    # Tokens da Stability AI começam com 'sk-'
    if not token.startswith('sk-'):
        return False, f"Token inválido: Tokens da Stability AI devem começar com 'sk-'. Token fornecido começa com '{token[:3]}...'"
    
    if len(token) < 40:
        return False, "Token muito curto para ser um token válido da Stability AI"
    
    return True, ""

def validar_token_openai(token: Optional[str]) -> Tuple[bool, str]:
    """
    Valida se o token da OpenAI está no formato correto.
    
    Args:
        token: Token a ser validado
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not token:
        return False, "Token não configurado"
    
    token = token.strip()
    
    # Tokens da OpenAI podem começar com 'sk-' ou 'sk-proj-'
    if not (token.startswith('sk-') or token.startswith('sk-proj-')):
        return False, f"Token inválido: Tokens da OpenAI devem começar com 'sk-' ou 'sk-proj-'. Token fornecido começa com '{token[:8]}...'"
    
    return True, ""

def validar_api_key(api_key: Optional[str], nome_servico: str) -> Tuple[bool, str]:
    """
    Validação genérica de API key.
    
    Args:
        api_key: Chave a ser validada
        nome_servico: Nome do serviço para mensagens de erro
        
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    if not api_key:
        return False, f"{nome_servico} não configurado"
    
    api_key = api_key.strip()
    
    if len(api_key) < 10:
        return False, f"API key muito curta para {nome_servico}"
    
    return True, ""

def verificar_configuracao_modelo(env_var: str, validar_formato: bool = False) -> Tuple[Optional[str], bool, str]:
    """
    Verifica se uma variável de ambiente está configurada e opcionalmente valida o formato.
    
    Args:
        env_var: Nome da variável de ambiente
        validar_formato: Se True, valida o formato baseado no nome da variável
        
    Returns:
        Tupla (valor, está_válido, mensagem_erro)
    """
    token = os.getenv(env_var)
    
    if not token:
        return None, False, f"{env_var} não configurado"
    
    token = token.strip()
    
    if validar_formato:
        if env_var in ("STABILITY_AI_API_KEY", "STABILITY_API_KEY"):
            is_valid, error_msg = validar_token_stability_ai(token)
            return token, is_valid, error_msg
        elif env_var == "OPENAI_API_KEY":
            is_valid, error_msg = validar_token_openai(token)
            return token, is_valid, error_msg
    
    return token, True, ""

