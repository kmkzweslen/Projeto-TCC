"""
Autenticação via Meta (Facebook Login) para contas Instagram Business/Creator.
"""
import secrets
import requests
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode
import jwt
from fastapi import HTTPException

from app.core import config
from app.services.user_service import (
    salvar_ou_atualizar_usuario,
    buscar_usuario_por_id,
)

_oauth_states: dict[str, datetime] = {}

INSTAGRAM_SCOPES = [
    "instagram_basic",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
    "business_management",
]


def _graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{config.META_GRAPH_VERSION}/{path}"


def gerar_url_login() -> tuple[str, str]:
    if not config.META_APP_ID or not config.META_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="META_APP_ID e META_APP_SECRET devem estar configurados no .env",
        )

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.utcnow() + timedelta(minutes=10)

    params = {
        "client_id": config.META_APP_ID,
        "redirect_uri": config.META_REDIRECT_URI,
        "scope": ",".join(INSTAGRAM_SCOPES),
        "response_type": "code",
        "state": state,
    }
    url = f"https://www.facebook.com/{config.META_GRAPH_VERSION}/dialog/oauth?{urlencode(params)}"
    return url, state


def _validar_state(state: str) -> bool:
    expira = _oauth_states.pop(state, None)
    if not expira:
        return False
    return datetime.utcnow() <= expira


def trocar_code_por_token(code: str) -> dict:
    params = {
        "client_id": config.META_APP_ID,
        "client_secret": config.META_APP_SECRET,
        "redirect_uri": config.META_REDIRECT_URI,
        "code": code,
    }
    resp = requests.get(_graph_url("oauth/access_token"), params=params, timeout=30)
    data = resp.json()
    if "access_token" not in data:
        raise HTTPException(
            status_code=400,
            detail=f"Falha ao obter token: {data.get('error', data)}",
        )
    return data


def obter_token_longa_duracao(short_token: str) -> dict:
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": config.META_APP_ID,
        "client_secret": config.META_APP_SECRET,
        "fb_exchange_token": short_token,
    }
    resp = requests.get(_graph_url("oauth/access_token"), params=params, timeout=30)
    data = resp.json()
    if "access_token" not in data:
        raise HTTPException(
            status_code=400,
            detail=f"Falha ao obter token de longa duração: {data.get('error', data)}",
        )
    return data


def obter_perfil_facebook(access_token: str) -> dict:
    resp = requests.get(
        _graph_url("me"),
        params={"fields": "id,name", "access_token": access_token},
        timeout=30,
    )
    data = resp.json()
    if "id" not in data:
        raise HTTPException(status_code=400, detail=f"Falha ao obter perfil: {data}")
    return data


def obter_conta_instagram(access_token: str) -> dict:
    """
    Obtém page_id, ig_user_id e username da primeira página com conta Instagram vinculada.
    """
    resp = requests.get(
        _graph_url("me/accounts"),
        params={
            "fields": "id,name,access_token,instagram_business_account",
            "access_token": access_token,
        },
        timeout=30,
    )
    pages_data = resp.json()
    if "error" in pages_data:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao listar páginas: {pages_data['error']}",
        )

    pages = pages_data.get("data", [])
    if not pages:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhuma Página do Facebook encontrada. "
                "Vincule uma Página à sua conta Instagram Business/Creator."
            ),
        )

    for page in pages:
        ig_account = page.get("instagram_business_account")
        if not ig_account:
            continue

        ig_id = ig_account.get("id")
        page_token = page.get("access_token", access_token)

        ig_resp = requests.get(
            _graph_url(ig_id),
            params={"fields": "id,username", "access_token": page_token},
            timeout=30,
        )
        ig_data = ig_resp.json()

        return {
            "page_id": page["id"],
            "page_name": page.get("name"),
            "ig_user_id": ig_id,
            "instagram_username": ig_data.get("username"),
            "access_token": page_token,
        }

    raise HTTPException(
        status_code=400,
        detail=(
            "Nenhuma conta Instagram Business vinculada a uma Página do Facebook. "
            "Configure sua conta em Meta Business Suite."
        ),
    )


def processar_callback(code: str, state: str) -> dict:
    if not _validar_state(state):
        raise HTTPException(status_code=400, detail="State inválido ou expirado.")

    short = trocar_code_por_token(code)
    long_lived = obter_token_longa_duracao(short["access_token"])
    access_token = long_lived["access_token"]
    expires_in = long_lived.get("expires_in", 5184000)  # ~60 dias

    perfil = obter_perfil_facebook(access_token)
    instagram = obter_conta_instagram(access_token)

    usuario = salvar_ou_atualizar_usuario({
        "facebook_id": perfil["id"],
        "nome": perfil.get("name"),
        "instagram_username": instagram.get("instagram_username"),
        "ig_user_id": instagram["ig_user_id"],
        "page_id": instagram["page_id"],
        "page_name": instagram.get("page_name"),
        "access_token": instagram["access_token"],
        "token_expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
    })

    jwt_token = criar_token_jwt(usuario["id"])
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "usuario": usuario,
    }


def criar_token_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=config.JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        usuario = buscar_usuario_por_id(user_id)
        if not usuario:
            return None
        usuario["id"] = user_id
        return usuario
    except jwt.PyJWTError:
        return None
