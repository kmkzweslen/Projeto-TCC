"""Schemas das respostas da API de geração."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Conformidade(BaseModel):
    caracteres: int
    emojis: int
    hashtags: int
    ctas_detectadas: int
    regras: Dict[str, bool]
    conforme: bool


class ImagemGerada(BaseModel):
    provedor: str
    modelo: str
    status: str
    url_publica: Optional[str] = None
    cloud_info: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None
    tempo_s: Optional[float] = None
    tempo_geracao_s: Optional[float] = None
    error: Optional[str] = None


class LegendaGerada(BaseModel):
    provedor: str
    modelo: str
    status: str
    legenda: Optional[str] = None
    conformidade: Optional[Conformidade] = None
    tempo_s: Optional[float] = None
    error: Optional[str] = None


class RespostaMultiModelo(BaseModel):
    tipo: str
    imagens: List[ImagemGerada] = []
    legendas: List[LegendaGerada] = []
    imagens_falhas: List[ImagemGerada] = []
    legendas_falhas: List[LegendaGerada] = []
    total_combinacoes: int = 0
    prompt_legenda: Optional[str] = None
    tempo_total_s: Optional[float] = None
    conteudo_id: Optional[str] = None
