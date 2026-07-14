from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.schemas.auth import LoginUrlResponse, UsuarioResponse
from app.services.auth_service import gerar_url_login, processar_callback
from app.services.user_service import usuario_para_resposta
from app.dependencies.auth import get_current_user
from app.core import config
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/instagram/login", response_model=LoginUrlResponse)
def instagram_login():
    """
    Retorna a URL para o usuário autorizar o app no Facebook/Instagram.
    Abra `authorization_url` no navegador.
    """
    url, state = gerar_url_login()
    return LoginUrlResponse(authorization_url=url, state=state)


@router.get("/instagram/callback")
def instagram_callback(
    code: str = Query(..., description="Código OAuth retornado pela Meta"),
    state: str = Query(..., description="State enviado no login"),
    redirect: bool = Query(False, description="Se true, redireciona para FRONTEND_URL com o token"),
):
    """
    Callback OAuth. Troca o code por token, vincula conta Instagram e retorna JWT.
    """
    resultado = processar_callback(code, state)
    token = resultado["access_token"]

    if redirect and config.FRONTEND_URL:
        return RedirectResponse(
            url=f"{config.FRONTEND_URL}?token={token}",
            status_code=302,
        )

    usuario = usuario_para_resposta(resultado["usuario"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_hours": config.JWT_EXPIRE_HOURS,
        "usuario": usuario,
    }


@router.get("/me", response_model=UsuarioResponse)
def obter_usuario_atual(usuario: dict = Depends(get_current_user)):
    """Retorna dados do usuário logado e status da conexão Instagram."""
    return usuario_para_resposta(usuario)
