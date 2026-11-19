from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.schemas.auth import LoginUrlResponse, UsuarioResponse
from app.services.auth_service import gerar_url_login, processar_callback
from app.services.user_service import usuario_para_resposta
from app.dependencies.auth import get_current_user
from app.core import config

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/instagram/login", response_model=LoginUrlResponse)
def instagram_login():
    """
    Retorna a URL para o usuário autorizar o app no Facebook/Instagram.
    Abra `authorization_url` no navegador.
    """
    url, state = gerar_url_login()
    return LoginUrlResponse(authorization_url=url, state=state)


def _voltar_ao_frontend(fragmento: str) -> RedirectResponse:
    # Os dados vão no fragmento (#), que não é enviado ao servidor nem
    # registrado em logs de acesso, ao contrário da query string (?token=).
    return RedirectResponse(
        url=f"{config.FRONTEND_URL.rstrip('/')}/#{fragmento}",
        status_code=302,
    )


def _mensagem_erro_meta(error, error_reason, error_description) -> str:
    if error_reason == "user_denied" or error == "access_denied":
        return (
            "A autorização foi cancelada. Para usar o sistema, clique em "
            "'Conectar com Instagram' e aceite as permissões até o fim."
        )
    return (
        f"A Meta não autorizou o login ({error}"
        f"{' / ' + error_reason if error_reason else ''}): "
        f"{error_description or 'sem descrição'}."
    )


@router.get("/instagram/callback")
def instagram_callback(
    code: str | None = Query(None, description="Código OAuth retornado pela Meta"),
    state: str | None = Query(None, description="State enviado no login"),
    error: str | None = Query(None, description="Erro devolvido pela Meta (ex.: access_denied)"),
    error_reason: str | None = Query(None),
    error_description: str | None = Query(None),
    redirect: bool | None = Query(
        None,
        description=(
            "Se omitido, redireciona para FRONTEND_URL quando ele está configurado. "
            "Use redirect=false para receber o JSON (testes pelo /docs)."
        ),
    ),
):
    """
    Callback OAuth. Troca o code por token, vincula conta Instagram e retorna JWT.

    Com FRONTEND_URL configurado, o navegador volta para o front-end com
    `#token=<jwt>` (sucesso) ou `#erro=<mensagem>` (falha), para que o usuário
    final nunca veja um JSON ou uma página de erro técnica.
    """
    usar_frontend = bool(config.FRONTEND_URL) and redirect is not False

    try:
        if error or not code or not state:
            # A Meta volta sem `code` quando o usuário cancela/recusa a autorização
            # ou quando há problema de configuração do app; nesse caso ela envia
            # error, error_reason e error_description no lugar do code.
            if error:
                detalhe = _mensagem_erro_meta(error, error_reason, error_description)
            else:
                detalhe = (
                    "Callback sem 'code'/'state'. Esta rota é aberta pela Meta ao fim do "
                    "login; não a acesse diretamente."
                )
            raise HTTPException(status_code=400, detail=detalhe)

        resultado = processar_callback(code, state)
    except HTTPException as e:
        if usar_frontend:
            return _voltar_ao_frontend(f"erro={quote(str(e.detail))}")
        raise

    token = resultado["access_token"]
    if usar_frontend:
        return _voltar_ao_frontend(f"token={token}")

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
