"""
Persistência de usuários e credenciais Instagram (MongoDB ou memória).
"""
from datetime import datetime
from typing import Optional, Dict
from app.services.database_service import get_mongo_client

_users_memory: Dict[str, dict] = {}


def _collection():
    _, db = get_mongo_client()
    if db is not None:
        return db["usuarios"]
    return None


def buscar_usuario_por_id(user_id: str) -> Optional[dict]:
    col = _collection()
    if col is not None:
        from bson import ObjectId
        try:
            doc = col.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        except Exception:
            pass
    return _users_memory.get(user_id)


def buscar_usuario_por_facebook_id(facebook_id: str) -> Optional[dict]:
    col = _collection()
    if col is not None:
        doc = col.find_one({"facebook_id": facebook_id})
        if doc:
            doc["id"] = str(doc["_id"])
            return doc
    for user in _users_memory.values():
        if user.get("facebook_id") == facebook_id:
            return user
    return None


def salvar_ou_atualizar_usuario(dados: dict) -> dict:
    """Cria ou atualiza usuário com credenciais Instagram."""
    col = _collection()
    agora = datetime.utcnow()

    documento = {
        "facebook_id": dados["facebook_id"],
        "nome": dados.get("nome"),
        "instagram_username": dados.get("instagram_username"),
        "ig_user_id": dados.get("ig_user_id"),
        "page_id": dados.get("page_id"),
        "page_name": dados.get("page_name"),
        "access_token": dados.get("access_token"),
        "token_expires_at": dados.get("token_expires_at"),
        "atualizado_em": agora,
    }

    if col is not None:
        existente = col.find_one({"facebook_id": dados["facebook_id"]})
        if existente:
            col.update_one({"_id": existente["_id"]}, {"$set": documento})
            documento["id"] = str(existente["_id"])
            documento["criado_em"] = existente.get("criado_em", agora)
        else:
            documento["criado_em"] = agora
            resultado = col.insert_one(documento)
            documento["id"] = str(resultado.inserted_id)
    else:
        existente = buscar_usuario_por_facebook_id(dados["facebook_id"])
        if existente:
            user_id = existente["id"]
            documento["id"] = user_id
            documento["criado_em"] = existente.get("criado_em", agora)
            _users_memory[user_id] = {**existente, **documento}
        else:
            import uuid
            user_id = str(uuid.uuid4())
            documento["id"] = user_id
            documento["criado_em"] = agora
            _users_memory[user_id] = documento

    return documento


def usuario_para_resposta(usuario: dict) -> dict:
    return {
        "id": usuario.get("id") or str(usuario.get("_id", "")),
        "nome": usuario.get("nome"),
        "instagram_username": usuario.get("instagram_username"),
        "instagram_conectado": bool(usuario.get("ig_user_id") and usuario.get("access_token")),
        "ig_user_id": usuario.get("ig_user_id"),
    }
