from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.conteudo import router as conteudo_router  # É só uma vez!

app = FastAPI(
    title="API Conteúdo com LLMs",
    description="Sistema multi-modelo para geração de conteúdo para Instagram",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conteudo_router, prefix="/api")

@app.get("/")
def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "API de Geração de Conteúdo com LLMs",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "gerar_conteudo": "POST /api/",
            "publicar_feed": "POST /api/instagram/publicar_feed"
        },
        "nota": "⚠️ Requisições de geração podem levar 2-3 minutos para completar"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
