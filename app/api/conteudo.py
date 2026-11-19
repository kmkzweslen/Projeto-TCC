from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.concurrency import run_in_threadpool

from app.core import config
from app.dependencies.auth import get_current_user
from app.schemas.auth import PublicarFeedRequest
from app.schemas.entrada import Entrada
from app.schemas.resposta import RespostaMultiModelo
from app.services.database_service import listar_historico, salvar_publicacao
from app.services.instagram_service import publicar_no_feed
from app.services.multi_model_service import (
    PROVEDORES_IMAGEM,
    PROVEDORES_TEXTO,
    gerar_conteudo_multi_modelo,
    persistir_resultado,
)

router = APIRouter()


@router.get("/status", tags=["Sistema"])
def status_provedores():
    """Provedores configurados e modelos em uso (não expõe chaves)."""
    return {
        "texto": [
            {"provedor": p.NOME, "modelo": p.modelo(), "configurado": p.disponivel()}
            for p in PROVEDORES_TEXTO
        ],
        "imagem": [
            {"provedor": p.NOME, "modelo": p.modelo(), "configurado": p.disponivel()}
            for p, _ in PROVEDORES_IMAGEM
        ],
        "hospedagem_imagens": bool(config.IMGBB_API_KEY),
        "banco_de_dados": bool(config.MONGODB_URI),
        "graph_api_version": config.META_GRAPH_VERSION,
    }


@router.post("/", response_model=RespostaMultiModelo, tags=["Conteúdo"])
async def gerar_conteudo_route(
    entrada: Entrada,
    usuario: dict = Depends(get_current_user),
):
    """
    Gera imagens e legendas com todos os provedores configurados (requer login).
    Depois, publique o par escolhido em POST /api/instagram/publicar_feed.
    """
    params = entrada.model_dump()
    try:
        resultado = await run_in_threadpool(gerar_conteudo_multi_modelo, params)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Erro ao gerar conteúdo: {e}")

    resultado["conteudo_id"] = await run_in_threadpool(
        persistir_resultado, resultado, params, usuario.get("id")
    )
    return resultado


@router.post("/instagram/publicar_feed", tags=["Instagram"])
async def publicar_feed(
    data: PublicarFeedRequest,
    usuario: dict = Depends(get_current_user),
):
    """
    Publica no feed do Instagram a imagem e a legenda escolhidas pelo usuário.
    Requer header: Authorization: Bearer <token>
    """
    if not usuario.get("ig_user_id") or not usuario.get("access_token"):
        raise HTTPException(
            status_code=400,
            detail="Conta do Instagram não vinculada. Faça login novamente em /api/auth/instagram/login",
        )

    resultado = await run_in_threadpool(
        publicar_no_feed,
        data.image_url,
        data.caption,
        usuario["ig_user_id"],
        usuario["access_token"],
    )

    await run_in_threadpool(salvar_publicacao, {
        "media_id": resultado.get("media_id"),
        "permalink": resultado.get("permalink"),
        "image_url": data.image_url,
        "caption": data.caption,
        "conteudo_id": data.conteudo_id,
        "status": "error" if "error" in resultado else "success",
        "erro": resultado.get("error"),
        "tempo_s": resultado.get("tempo_s"),
        "usuario_id": usuario.get("id"),
    })

    if "error" in resultado:
        codigo = {"validacao": 422, "limite": 429}.get(resultado.get("etapa"), 502)
        raise HTTPException(status_code=codigo, detail=resultado)

    return {"mensagem": "Conteúdo publicado com sucesso no Instagram!", "publicacao": resultado}


@router.get("/historico", tags=["Conteúdo"])
async def historico(
    limite: int = Query(20, ge=1, le=100, description="Quantidade de gerações a listar"),
    usuario: dict = Depends(get_current_user),
):
    """Últimas gerações do usuário logado, com as publicações de cada uma."""
    itens = await run_in_threadpool(listar_historico, usuario.get("id"), limite)
    return {"itens": itens, "total": len(itens)}
