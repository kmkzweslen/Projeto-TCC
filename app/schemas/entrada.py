from pydantic import BaseModel, Field
from typing import Optional

class Entrada(BaseModel):
    """
    Schema de entrada usando metodologia Co-STAR para engenharia de prompt.
    
    Campos baseados em Co-STAR:
    - Context: rede_alvo, publico
    - Statement: tema, objetivo
    - Task: tipo, formato
    - Action: tom
    - Result: (implícito na combinação dos campos)
    """
    tema: str = Field(
        ..., 
        description="Tema principal do conteúdo (ex: 'beleza', 'tecnologia', 'culinária')",
        example="beleza"
    )
    tipo: str = Field(
        ..., 
        description="Tipo de conteúdo a ser gerado",
        example="imagem"
    )
    objetivo: str = Field(
        ..., 
        description="Objetivo do conteúdo (ex: 'atrair seguidores', 'vender produto', 'educar público')",
        example="atrair seguidores"
    )
    publico: str = Field(
        ..., 
        description="Público-alvo detalhado (ex: 'mulheres entre 20 e 30 anos', 'empreendedores iniciantes')",
        example="mulheres entre 20 e 30 anos"
    )
    tom: str = Field(
        ..., 
        description="Tom de voz desejado (ex: 'casual', 'profissional', 'descontraído', 'inspirador')",
        example="casual"
    )
    rede_alvo: str = Field(
        ..., 
        description="Rede social destino (ex: 'Instagram', 'Facebook', 'LinkedIn')",
        example="Instagram"
    )
    formato: str = Field(
        ..., 
        description="Formato do conteúdo (ex: 'quadrado', 'carrossel', 'stories', 'reels')",
        example="carrossel"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "tema": "beleza",
                "tipo": "imagem",
                "objetivo": "atrair seguidores",
                "publico": "mulheres solteiras entre 20 e 30 anos",
                "tom": "casual",
                "rede_alvo": "Instagram",
                "formato": "carrossel"
            }
        }
