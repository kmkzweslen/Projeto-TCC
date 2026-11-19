"""
Criptografia simétrica (Fernet) dos tokens de acesso da Meta salvos no banco.

Os tokens permitem publicar em nome do usuário, então não devem ficar em texto
puro no MongoDB. Valores criptografados recebem o prefixo "enc:"; valores
antigos sem o prefixo continuam sendo lidos (compatibilidade com registros
gravados antes desta mudança).
"""
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core import config

_PREFIXO = "enc:"
_fernet: Optional[Fernet] = None


def _obter_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if config.TOKEN_ENCRYPTION_KEY:
            chave = config.TOKEN_ENCRYPTION_KEY.encode()
        else:
            # Deriva uma chave Fernet válida (32 bytes, base64) do segredo JWT.
            digest = hashlib.sha256(("token-encryption:" + config.JWT_SECRET_KEY).encode()).digest()
            chave = base64.urlsafe_b64encode(digest)
        _fernet = Fernet(chave)
    return _fernet


def criptografar(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return valor
    if valor.startswith(_PREFIXO):
        return valor
    return _PREFIXO + _obter_fernet().encrypt(valor.encode()).decode()


def descriptografar(valor: Optional[str]) -> Optional[str]:
    """
    Retorna o valor original. Se o valor estiver em texto puro (registro antigo),
    devolve-o como está. Se a chave mudou e não for possível descriptografar,
    retorna None (o usuário precisará fazer login novamente).
    """
    if not valor:
        return valor
    if not valor.startswith(_PREFIXO):
        return valor
    try:
        return _obter_fernet().decrypt(valor[len(_PREFIXO):].encode()).decode()
    except InvalidToken:
        return None
