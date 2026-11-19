"""
Conexão e operações com o MongoDB.

Se MONGODB_URI não estiver configurado, as funções de gravação apenas
retornam None, e a aplicação continua funcionando (sem persistência).
"""
from datetime import datetime, timezone
from typing import Dict, Optional

from app.core import config

_mongo_client = None
_db = None


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def get_mongo_client():
    """Retorna (cliente, banco), criando a conexão na primeira chamada."""
    global _mongo_client, _db

    if not config.MONGODB_URI:
        return None, None

    if _mongo_client is None:
        try:
            from pymongo import MongoClient

            _mongo_client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            _db = _mongo_client[config.MONGODB_DB_NAME]
            print("✅ Conectado ao MongoDB")
        except Exception as e:
            print(f"⚠️ Erro ao conectar ao MongoDB: {e}")
            return None, None

    return _mongo_client, _db


def _inserir(colecao: str, documento: Dict) -> Optional[str]:
    _, db = get_mongo_client()
    if db is None:
        return None
    try:
        resultado = db[colecao].insert_one(documento)
        return str(resultado.inserted_id)
    except Exception as e:
        print(f"⚠️ Erro ao salvar em '{colecao}': {e}")
        return None


def _parametros(dados: Dict) -> Dict:
    """Campos de entrada (CO-STAR) gravados junto com cada registro."""
    campos = ("tema", "tipo", "objetivo", "publico", "tom", "rede_alvo", "formato")
    return {campo: dados.get(campo) for campo in campos}


def salvar_imagem_gerada(imagem_data: Dict) -> Optional[str]:
    documento = {
        "modelo": imagem_data.get("modelo", "desconhecido"),
        "provedor": imagem_data.get("provedor"),
        "url_publica": imagem_data.get("url_publica"),
        "cloud_info": imagem_data.get("cloud_info", {}),
        "status": imagem_data.get("status", "unknown"),
        "erro": imagem_data.get("error"),
        "tempo_s": imagem_data.get("tempo_s"),
        "prompt": imagem_data.get("prompt"),
        "usuario_id": imagem_data.get("usuario_id"),
        "criado_em": _agora(),
        **_parametros(imagem_data),
    }
    return _inserir("imagens_geradas", documento)


def salvar_legenda_gerada(legenda_data: Dict) -> Optional[str]:
    documento = {
        "modelo": legenda_data.get("modelo", "desconhecido"),
        "provedor": legenda_data.get("provedor"),
        "legenda": legenda_data.get("legenda"),
        "status": legenda_data.get("status", "unknown"),
        "erro": legenda_data.get("error"),
        "tempo_s": legenda_data.get("tempo_s"),
        "conformidade": legenda_data.get("conformidade"),
        "usuario_id": legenda_data.get("usuario_id"),
        "criado_em": _agora(),
        **_parametros(legenda_data),
    }
    return _inserir("legendas_geradas", documento)


def salvar_conteudo_completo(conteudo_data: Dict) -> Optional[str]:
    documento = {
        "imagens": conteudo_data.get("imagens", []),
        "legendas": conteudo_data.get("legendas", []),
        "imagens_falhas": conteudo_data.get("imagens_falhas", []),
        "legendas_falhas": conteudo_data.get("legendas_falhas", []),
        "total_combinacoes": conteudo_data.get("total_combinacoes", 0),
        "tempo_total_s": conteudo_data.get("tempo_total_s"),
        "usuario_id": conteudo_data.get("usuario_id"),
        "criado_em": _agora(),
        **_parametros(conteudo_data),
    }
    return _inserir("conteudos_gerados", documento)


def salvar_publicacao(publicacao_data: Dict) -> Optional[str]:
    """Registra cada publicação feita (evidência do critério C3)."""
    documento = {
        "media_id": publicacao_data.get("media_id"),
        "permalink": publicacao_data.get("permalink"),
        "image_url": publicacao_data.get("image_url"),
        "caption": publicacao_data.get("caption"),
        "conteudo_id": publicacao_data.get("conteudo_id"),
        "status": publicacao_data.get("status"),
        "erro": publicacao_data.get("erro"),
        "tempo_s": publicacao_data.get("tempo_s"),
        "usuario_id": publicacao_data.get("usuario_id"),
        "criado_em": _agora(),
    }
    return _inserir("publicacoes", documento)


def _serializar(valor):
    """Converte ObjectId/datetime para tipos que o JSON aceita."""
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {k: _serializar(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_serializar(v) for v in valor]
    if type(valor).__name__ == "ObjectId":
        return str(valor)
    return valor


def listar_historico(usuario_id: Optional[str], limite: int = 20) -> list:
    """
    Últimos conteúdos gerados pelo usuário, do mais recente para o mais antigo,
    cada um com as publicações feitas a partir dele (vinculadas por conteudo_id).
    """
    _, db = get_mongo_client()
    if db is None or not usuario_id:
        return []
    limite = max(1, min(int(limite), 100))
    try:
        conteudos = list(
            db["conteudos_gerados"]
            .find({"usuario_id": usuario_id})
            .sort("criado_em", -1)
            .limit(limite)
        )
        ids = [str(c["_id"]) for c in conteudos]
        publicacoes = {}
        if ids:
            for pub in db["publicacoes"].find({"conteudo_id": {"$in": ids}}).sort("criado_em", 1):
                publicacoes.setdefault(pub.get("conteudo_id"), []).append(pub)

        historico = []
        for c in conteudos:
            cid = str(c["_id"])
            item = {campo: c.get(campo) for campo in (
                "tema", "objetivo", "publico", "tom", "imagens", "legendas",
                "imagens_falhas", "legendas_falhas", "tempo_total_s", "criado_em",
            )}
            item["id"] = cid
            item["publicacoes"] = [
                {campo: p.get(campo) for campo in (
                    "status", "permalink", "media_id", "image_url", "caption",
                    "erro", "tempo_s", "criado_em",
                )}
                for p in publicacoes.get(cid, [])
            ]
            historico.append(_serializar(item))
        return historico
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Erro ao ler o histórico: {e}")
        return []
