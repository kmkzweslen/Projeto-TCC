from pydantic import BaseModel, Field
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


class PublicarFeedRequest(BaseModel):
    image_url: str = Field(..., description="URL pública da imagem (ex: ImgBB)")
    caption: str = Field(..., description="Legenda do post")
