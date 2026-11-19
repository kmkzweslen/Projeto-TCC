from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LoginUrlResponse(BaseModel):
    authorization_url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int


class UsuarioResponse(BaseModel):
    id: str
    nome: Optional[str] = None
    instagram_username: Optional[str] = None
    instagram_conectado: bool = False
    ig_user_id: Optional[str] = None
    page_name: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class PublicarFeedRequest(BaseModel):
    image_url: str = Field(..., description="URL pública HTTPS da imagem (ex.: retornada pelo ImgBB)")
    caption: str = Field(..., min_length=1, max_length=2200, description="Legenda do post (máx. 2.200 caracteres)")
    conteudo_id: Optional[str] = Field(None, description="Id do conteúdo gerado (para vincular a publicação no banco)")
