from pydantic import BaseModel, Field
from typing import Optional

class EdicaoImagemEntrada(BaseModel):
    """
    Schema para edição de imagem com upload e prompt.
    """
    prompt: str = Field(
        ...,
        description="Prompt descrevendo as alterações desejadas na imagem",
        example="adicionar efeito de neblina ao fundo, tornar cores mais vibrantes"
    )
    strength: Optional[float] = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Força da edição (0.0 = mantém imagem original, 1.0 = transformação total)",
        example=0.7
    )
    num_outputs: Optional[int] = Field(
        1,
        ge=1,
        le=4,
        description="Número de variações a gerar",
        example=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "adicionar efeito de neblina ao fundo, tornar cores mais vibrantes",
                "strength": 0.7,
                "num_outputs": 1
            }
        }
