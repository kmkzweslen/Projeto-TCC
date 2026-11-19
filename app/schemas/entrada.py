"""
Entrada da geração de conteúdo.

Os sete campos alimentam os componentes do framework CO-STAR
(ver app/utils/prompt_engineering.py):
  Context   <- rede_alvo, tema
  Objective <- objetivo
  Style     <- formato
  Tone      <- tom
  Audience  <- publico
  Response  <- regras fixas (tamanho, emojis, hashtags e uma CTA)
O campo "tipo" define se serão geradas imagens ("imagem") ou só legendas ("texto").
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Entrada(BaseModel):
    tema: str = Field(..., min_length=2, max_length=200,
                      description="Tema principal do conteúdo (ex.: 'lançamento da coleção de verão')")
    tipo: Literal["imagem", "texto"] = Field(
        "imagem", description="'imagem' gera imagens e legendas; 'texto' gera apenas legendas")
    objetivo: str = Field(..., min_length=2, max_length=200,
                          description="Objetivo da publicação (ex.: 'vender produto', 'educar o público')")
    publico: str = Field(..., min_length=2, max_length=200,
                         description="Público-alvo (ex.: 'mulheres de 20 a 35 anos')")
    tom: str = Field(..., min_length=2, max_length=100,
                     description="Tom de voz (ex.: 'descontraído', 'profissional', 'acolhedor')")
    rede_alvo: str = Field("Instagram", max_length=50,
                           description="Rede social de destino (a publicação é suportada apenas no Instagram)")
    formato: str = Field("post de feed com imagem única", max_length=100,
                         description="Formato da publicação (a publicação automática suporta post de feed com imagem única)")

    @field_validator("tipo", mode="before")
    @classmethod
    def _normalizar_tipo(cls, valor):
        return valor.strip().lower() if isinstance(valor, str) else valor

    @field_validator("tema", "objetivo", "publico", "tom", "rede_alvo", "formato")
    @classmethod
    def _limpar_texto(cls, valor: str) -> str:
        # Remove quebras de linha e espaços extras para não deformar o prompt.
        return " ".join(valor.split())

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "tema": "lançamento da coleção de verão",
            "tipo": "imagem",
            "objetivo": "vender produto",
            "publico": "mulheres de 20 a 35 anos",
            "tom": "descontraído",
            "rede_alvo": "Instagram",
            "formato": "post de feed com imagem única",
        }
    })
