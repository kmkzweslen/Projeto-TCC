"""
Persistência de usuários e credenciais do Instagram (MongoDB ou memória).

O token de acesso da Meta é gravado criptografado (ver app/utils/criptografia.py)
e só é descriptografado ao ser lido pelos serviços.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from app.services.database_service import get_mongo_client
from app.utils.criptografia import criptografar, descriptografar

_users_memory: Dict[str, dict] = {}


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _collection():
    _, db = get_mongo_client()
    if db is not None:
        return db["usuarios"]
    return None


def _preparar_leitura(doc: Optional[dict]) -> Optional[dict]:
    """Converte o documento do banco para uso interno (id e token legível)."""
    if not doc:
        return None
    usuario = dict(doc)
    if "_id" in usuario:
        usuario["id"] = str(usuario["_id"])
    usuario["access_token"] = descriptografar(usuario.get("access_token"))
    return usuario


def buscar_usuario_por_id(user_id: str) -> Optional[dict]:
    col = _collection()
    if col is not None:
        from bson import ObjectId
        from bson.errors import InvalidId

        try:
            return _preparar_leitura(col.find_one({"_id": ObjectId(user_id)}))
        except InvalidId:
            return None
    return _preparar_leitura(_users_memory.get(user_id))


def buscar_usuario_por_facebook_id(facebook_id: str) -> Optional[dict]:
    col = _collection()
    if col is not None:
        return _preparar_leitura(col.find_one({"facebook_id": facebook_id}))
    for user in _users_memory.values():
        if user.get("facebook_id") == facebook_id:
            return _preparar_leitura(user)
    return None


def salvar_ou_atualizar_usuario(dados: dict) -> dict:
    """Cria ou atualiza o usuário com as credenciais do Instagram."""
    col = _collection()
    agora = _agora()

    documento = {
        "facebook_id": dados["facebook_id"],
        "nome": dados.get("nome"),
        "instagram_username": dados.get("instagram_username"),
        "ig_user_id": dados.get("ig_user_id"),
        "page_id": dados.get("page_id"),
        "page_name": dados.get("page_name"),
        "access_token": criptografar(dados.get("access_token")),
        "token_expires_at": dados.get("token_expires_at"),
        "atualizado_em": agora,
    }

    if col is not None:
        existente = col.find_one({"facebook_id": dados["facebook_id"]})
        if existente:
            col.update_one({"_id": existente["_id"]}, {"$set": documento})
            documento["_id"] = existente["_id"]
            documento["criado_em"] = existente.get("criado_em", agora)
        else:
            documento["criado_em"] = agora
            resultado = col.insert_one(documento)
            documento["_id"] = resultado.inserted_id
    else:
        existente = next(
            (u for u in _users_memory.values() if u.get("facebook_id") == dados["facebook_id"]),
            None,
        )
        if existente:
            documento["id"] = existente["id"]
            documento["criado_em"] = existente.get("criado_em", agora)
        else:
            documento["id"] = str(uuid.uuid4())
            documento["criado_em"] = agora
        _users_memory[documento["id"]] = documento

    return _preparar_leitura(documento)


def usuario_para_resposta(usuario: dict) -> dict:
    """Dados públicos do usuário (nunca inclui o token)."""
    return {
        "id": usuario.get("id") or str(usuario.get("_id", "")),
        "nome": usuario.get("nome"),
        "instagram_username": usuario.get("instagram_username"),
        "instagram_conectado": bool(usuario.get("ig_user_id") and usuario.get("access_token")),
        "ig_user_id": usuario.get("ig_user_id"),
        "page_name": usuario.get("page_name"),
        "token_expires_at": usuario.get("token_expires_at"),
    }
