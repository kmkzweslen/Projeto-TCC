"""
Schemas para respostas da API
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ImagemGerada(BaseModel):
    """Modelo para uma imagem gerada"""
    modelo: str
    url_publica: Optional[str] = None
    url_temporaria: Optional[str] = None
    public_id: Optional[str] = None
    cloud_info: Optional[Dict[str, Any]] = None
    status: str
    error: Optional[str] = None

class LegendaGerada(BaseModel):
    """Modelo para uma legenda gerada"""
    modelo: str
    legenda: Optional[str] = None
    status: str
    error: Optional[str] = None

class RespostaMultiModelo(BaseModel):
    """Resposta com todas as opções geradas pelos múltiplos modelos"""
    tipo: str
    imagens: List[ImagemGerada] = []
    legendas: List[LegendaGerada] = []
    imagens_falhas: List[Dict[str, Any]] = []
    legendas_falhas: List[Dict[str, Any]] = []
    total_combinacoes: int = 0

