"""Funções auxiliares para chamadas HTTP aos provedores de IA."""
import requests


def mensagem_de_erro(resposta: requests.Response) -> str:
    """Extrai uma mensagem legível do corpo de erro de uma API."""
    try:
        corpo = resposta.json()
    except ValueError:
        return f"HTTP {resposta.status_code}: {resposta.text[:300]}"

    erro = corpo.get("error") if isinstance(corpo, dict) else None
    if isinstance(erro, dict):
        return f"HTTP {resposta.status_code}: {erro.get('message', erro)}"
    if isinstance(corpo, dict) and corpo.get("errors"):
        return f"HTTP {resposta.status_code}: {corpo['errors']}"
    if isinstance(corpo, dict) and corpo.get("message"):
        return f"HTTP {resposta.status_code}: {corpo['message']}"
    return f"HTTP {resposta.status_code}: {str(corpo)[:300]}"
