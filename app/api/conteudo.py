from fastapi import APIRouter, HTTPException, Depends
from app.schemas.entrada import Entrada
from app.schemas.auth import PublicarFeedRequest
from app.services.multi_model_service import gerar_conteudo_multi_modelo
from app.services.instagram_service import publicar_no_feed
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.post("/instagram/publicar_feed")
def publicar_feed(
    data: PublicarFeedRequest,
    usuario: dict = Depends(get_current_user),
):
    """
    Publica no feed do Instagram usando a conta do usuário logado.
    Requer header: Authorization: Bearer <token>
    """
    if not usuario.get("ig_user_id") or not usuario.get("access_token"):
        raise HTTPException(
            status_code=400,
            detail="Conta Instagram não vinculada. Faça login novamente em /api/auth/instagram/login",
        )

    resultado = publicar_no_feed(
        image_url=data.image_url,
        caption=data.caption,
        ig_user_id=usuario["ig_user_id"],
        access_token=usuario["access_token"],
    )

    if "error" in resultado:
        raise HTTPException(status_code=502, detail=resultado)

    return {
        "mensagem": "Conteúdo publicado com sucesso no Instagram!",
        "publicacao": resultado,
    }


@router.post("/")
async def gerar_conteudo_route(
    entrada: Entrada,
    usuario: dict = Depends(get_current_user),
):
    """
    Gera imagens e legendas com IA (requer login).
    Após gerar, use POST /api/instagram/publicar_feed com a imagem e legenda escolhidas.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            resultado = await loop.run_in_executor(
                executor,
                gerar_conteudo_multi_modelo,
                entrada.dict(),
            )

        try:
            from app.services.database_service import (
                salvar_conteudo_completo,
                salvar_imagem_gerada,
                salvar_legenda_gerada,
            )

            dados_para_salvar = resultado.copy()
            dados_para_salvar.update(entrada.dict())
            dados_para_salvar["usuario_id"] = usuario.get("id")

            conteudo_id = salvar_conteudo_completo(dados_para_salvar)

            for imagem in resultado.get("imagens", []):
                imagem_data = imagem.copy()
                imagem_data.update(entrada.dict())
                imagem_data["usuario_id"] = usuario.get("id")
                salvar_imagem_gerada(imagem_data)

            for legenda in resultado.get("legendas", []):
                legenda_data = legenda.copy()
                legenda_data.update(entrada.dict())
                legenda_data["usuario_id"] = usuario.get("id")
                salvar_legenda_gerada(legenda_data)

            if conteudo_id:
                resultado["mongodb_id"] = conteudo_id
        except Exception as db_error:
            print(f"⚠️ Erro ao salvar no MongoDB (continuando): {str(db_error)}")

        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar conteúdo: {str(e)}")
