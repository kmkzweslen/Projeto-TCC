"""
Autenticação via Meta (Facebook Login) para contas Instagram Business/Creator.

Observação: os "states" do OAuth ficam em memória, o que pressupõe uma única
instância do servidor (adequado ao protótipo).
"""
import secrets
import requests
from datetime import datetime, timedelta, timezone
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



def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _limpar_states_expirados() -> None:
    agora = _agora()
    for state in [s for s, expira in _oauth_states.items() if expira < agora]:
        _oauth_states.pop(state, None)


def _graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{config.META_GRAPH_VERSION}/{path}"


def gerar_url_login() -> tuple[str, str]:
    if not config.META_APP_ID or not config.META_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="META_APP_ID e META_APP_SECRET devem estar configurados no .env",
        )

    _limpar_states_expirados()
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = _agora() + timedelta(minutes=10)

    params = {
        "client_id": config.META_APP_ID,
        "redirect_uri": config.META_REDIRECT_URI,
        "response_type": "code",
        "state": state,
    }
    if config.META_LOGIN_CONFIG_ID:
        # Login do Facebook para Empresas: as permissões vêm da configuração do painel.
        params["config_id"] = config.META_LOGIN_CONFIG_ID
    else:
        params["scope"] = ",".join(config.META_LOGIN_SCOPES)
    url = f"https://www.facebook.com/{config.META_GRAPH_VERSION}/dialog/oauth?{urlencode(params)}"
    return url, state


def _validar_state(state: str) -> bool:
    expira = _oauth_states.pop(state, None)
    if not expira:
        return False
    return _agora() <= expira


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


_CAMPOS_PAGINA = "id,name,access_token,instagram_business_account"


def _get_graph(caminho: str, access_token: str, **params) -> dict:
    resp = requests.get(
        _graph_url(caminho),
        params={**params, "access_token": access_token},
        timeout=30,
    )
    try:
        return resp.json()
    except ValueError:
        return {"error": {"message": f"Resposta inválida da Graph API (HTTP {resp.status_code})"}}


def _paginas_do_usuario(access_token: str) -> list:
    """Páginas que o usuário administra diretamente (me/accounts)."""
    dados = _get_graph("me/accounts", access_token, fields=_CAMPOS_PAGINA, limit=100)
    if "error" in dados:
        raise HTTPException(status_code=400, detail=f"Erro ao listar páginas: {dados['error']}")
    return dados.get("data", [])


def _paginas_dos_portfolios(access_token: str) -> list:
    """
    Páginas de Portfólios Empresariais (Meta Business Suite) do usuário.
    Páginas que pertencem a um portfólio nem sempre aparecem em me/accounts.
    Requer a permissão business_management; sem ela a Graph API devolve erro,
    que é tratado como lista vazia (a busca segue só com me/accounts).
    """
    portfolios = _get_graph("me/businesses", access_token, fields="id,name", limit=100)
    paginas = []
    for portfolio in portfolios.get("data", []):
        for aresta in ("owned_pages", "client_pages"):
            dados = _get_graph(f"{portfolio['id']}/{aresta}", access_token, fields=_CAMPOS_PAGINA, limit=100)
            paginas.extend(dados.get("data", []))
    return paginas


def _permissoes_concedidas(access_token: str) -> str:
    dados = _get_graph("me/permissions", access_token)
    concedidas = [p["permission"] for p in dados.get("data", []) if p.get("status") == "granted"]
    recusadas = [p["permission"] for p in dados.get("data", []) if p.get("status") != "granted"]
    texto = f"Permissões concedidas: {', '.join(concedidas) or 'nenhuma'}."
    if recusadas:
        texto += f" Recusadas: {', '.join(recusadas)}."
    return texto


def obter_conta_instagram(access_token: str) -> dict:
    """
    Obtém page_id, ig_user_id e username da primeira Página com conta do
    Instagram profissional vinculada. Procura primeiro nas Páginas do usuário
    e, se não encontrar, nas Páginas dos seus Portfólios Empresariais.
    """
    paginas = _paginas_do_usuario(access_token)
    if not any(p.get("instagram_business_account") for p in paginas):
        paginas += _paginas_dos_portfolios(access_token)

    for page in paginas:
        ig_account = page.get("instagram_business_account")
        if not ig_account:
            continue

        ig_id = ig_account.get("id")
        page_token = page.get("access_token")
        if not page_token:
            page_token = _get_graph(page["id"], access_token, fields="access_token").get("access_token")
        page_token = page_token or access_token

        ig_data = _get_graph(ig_id, page_token, fields="id,username")
        return {
            "page_id": page["id"],
            "page_name": page.get("name"),
            "ig_user_id": ig_id,
            "instagram_username": ig_data.get("username"),
            "access_token": page_token,
        }

    if not paginas:
        detalhe = (
            "Nenhuma Página do Facebook encontrada (nem nas suas Páginas nem nos seus "
            "Portfólios Empresariais). Verifique se o Instagram profissional está "
            "vinculado a uma Página e se você marcou essa Página ao autorizar o app. "
        )
    else:
        nomes = ", ".join(p.get("name", p["id"]) for p in paginas)
        detalhe = (
            f"Páginas encontradas ({nomes}), mas nenhuma tem conta do Instagram "
            "profissional vinculada. Vincule pelo Instagram (Configurações > Central de "
            "Contas) ou pela Meta Business Suite. "
        )
    raise HTTPException(status_code=400, detail=detalhe + _permissoes_concedidas(access_token))


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
        "token_expires_at": _agora() + timedelta(seconds=expires_in),
    })

    jwt_token = criar_token_jwt(usuario["id"])
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "usuario": usuario,
    }


def criar_token_jwt(user_id: str) -> str:
    agora = _agora()
    payload = {
        "sub": user_id,
        "exp": agora + timedelta(hours=config.JWT_EXPIRE_HOURS),
        "iat": agora,
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
        # Se o token da Meta não puder ser descriptografado (chave trocada),
        # access_token vem None e o Instagram aparece como desconectado.
        usuario["id"] = user_id
        return usuario
    except jwt.PyJWTError:
        return None
