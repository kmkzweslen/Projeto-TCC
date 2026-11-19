from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.conteudo import router as conteudo_router
from app.core import config

config.validar_configuracao()

app = FastAPI(
    title="API de Conteúdo com IA para Instagram",
    description=(
        "Gera legendas (CO-STAR + CTA) e imagens com múltiplos provedores de IA "
        "e publica o par escolhido no feed do Instagram."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Origens explícitas: allow_origins=["*"] junto com allow_credentials=True
# não é aceito pelos navegadores e deixaria a API aberta a qualquer site.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(conteudo_router, prefix="/api")


@app.get("/")
def root():
    """Informações gerais da API."""
    return {
        "message": "API de Geração de Conteúdo com IA para Instagram",
        "version": app.version,
        "docs": "/docs",
        "endpoints": {
            "login_instagram": "GET /api/auth/instagram/login",
            "callback_oauth": "GET /api/auth/instagram/callback",
            "usuario_atual": "GET /api/auth/me",
            "status_provedores": "GET /api/status",
            "gerar_conteudo": "POST /api/ (requer Bearer token)",
            "publicar_feed": "POST /api/instagram/publicar_feed (requer Bearer token)",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
