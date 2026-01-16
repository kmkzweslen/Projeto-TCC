"""
Serviço de conexão e operações com MongoDB
"""
import os
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "prototipo")

# Cliente MongoDB será criado quando necessário
_mongo_client = None
_db = None


def get_mongo_client():
    """Retorna o cliente MongoDB, criando se necessário."""
    global _mongo_client, _db
    
    if not MONGODB_URI:
        return None, None
    
    if _mongo_client is None:
        try:
            from pymongo import MongoClient
            _mongo_client = MongoClient(MONGODB_URI)
            _db = _mongo_client[MONGODB_DB_NAME]
            print("✅ Conectado ao MongoDB")
        except Exception as e:
            print(f"⚠️ Erro ao conectar ao MongoDB: {str(e)}")
            return None, None
    
    return _mongo_client, _db


def salvar_imagem_gerada(imagem_data: Dict) -> Optional[str]:
    """
    Salva uma imagem gerada no MongoDB.
    
    Args:
        imagem_data: Dicionário com dados da imagem (modelo, url_publica, status, etc.)
    
    Returns:
        str: ID do documento salvo ou None se falhar
    """
    client, db = get_mongo_client()
    
    if db is None:
        print("⚠️ MongoDB não configurado. Pulando salvamento.")
        return None
    
    try:
        collection = db["imagens_geradas"]
        
        documento = {
            "modelo": imagem_data.get("modelo", "desconhecido"),
            "url_publica": imagem_data.get("url_publica"),
            "url_temporaria": imagem_data.get("url_temporaria"),
            "public_id": imagem_data.get("public_id"),
            "cloud_info": imagem_data.get("cloud_info", {}),
            "status": imagem_data.get("status", "unknown"),
            "erro": imagem_data.get("error"),
            "criado_em": datetime.utcnow(),
            "tema": imagem_data.get("tema"),
            "publico": imagem_data.get("publico"),
            "rede_alvo": imagem_data.get("rede_alvo")
        }
        
        resultado = collection.insert_one(documento)
        print(f"✅ Imagem salva no MongoDB: {resultado.inserted_id}")
        return str(resultado.inserted_id)
    
    except Exception as e:
        print(f"⚠️ Erro ao salvar imagem no MongoDB: {str(e)}")
        return None


def salvar_legenda_gerada(legenda_data: Dict) -> Optional[str]:
    """
    Salva uma legenda gerada no MongoDB.
    
    Args:
        legenda_data: Dicionário com dados da legenda (modelo, legenda, status, etc.)
    
    Returns:
        str: ID do documento salvo ou None se falhar
    """
    client, db = get_mongo_client()
    
    if db is None:
        print("⚠️ MongoDB não configurado. Pulando salvamento.")
        return None
    
    try:
        collection = db["legendas_geradas"]
        
        documento = {
            "modelo": legenda_data.get("modelo", "desconhecido"),
            "legenda": legenda_data.get("legenda"),
            "status": legenda_data.get("status", "unknown"),
            "erro": legenda_data.get("error"),
            "criado_em": datetime.utcnow(),
            "tema": legenda_data.get("tema"),
            "tipo": legenda_data.get("tipo"),
            "objetivo": legenda_data.get("objetivo"),
            "publico": legenda_data.get("publico"),
            "tom": legenda_data.get("tom"),
            "rede_alvo": legenda_data.get("rede_alvo"),
            "formato": legenda_data.get("formato")
        }
        
        resultado = collection.insert_one(documento)
        print(f"✅ Legenda salva no MongoDB: {resultado.inserted_id}")
        return str(resultado.inserted_id)
    
    except Exception as e:
        print(f"⚠️ Erro ao salvar legenda no MongoDB: {str(e)}")
        return None


def salvar_conteudo_completo(conteudo_data: Dict) -> Optional[str]:
    """
    Salva um conteúdo completo (imagens + legendas) no MongoDB.
    
    Args:
        conteudo_data: Dicionário com dados completos do conteúdo gerado
    
    Returns:
        str: ID do documento salvo ou None se falhar
    """
    client, db = get_mongo_client()
    
    if db is None:
        print("⚠️ MongoDB não configurado. Pulando salvamento.")
        return None
    
    try:
        collection = db["conteudos_gerados"]
        
        documento = {
            "tipo": conteudo_data.get("tipo"),
            "tema": conteudo_data.get("tema"),
            "objetivo": conteudo_data.get("objetivo"),
            "publico": conteudo_data.get("publico"),
            "tom": conteudo_data.get("tom"),
            "rede_alvo": conteudo_data.get("rede_alvo"),
            "formato": conteudo_data.get("formato"),
            "imagens": conteudo_data.get("imagens", []),
            "legendas": conteudo_data.get("legendas", []),
            "total_combinacoes": conteudo_data.get("total_combinacoes", 0),
            "criado_em": datetime.utcnow()
        }
        
        resultado = collection.insert_one(documento)
        print(f"✅ Conteúdo completo salvo no MongoDB: {resultado.inserted_id}")
        return str(resultado.inserted_id)
    
    except Exception as e:
        print(f"⚠️ Erro ao salvar conteúdo completo no MongoDB: {str(e)}")
        return None


def salvar_imagem_editada(edicao_data: Dict) -> Optional[str]:
    """
    Salva uma imagem editada no MongoDB.
    
    Args:
        edicao_data: Dicionário com dados da edição (prompt, imagens_editadas, etc.)
    
    Returns:
        str: ID do documento salvo ou None se falhar
    """
    client, db = get_mongo_client()
    
    if db is None:
        print("⚠️ MongoDB não configurado. Pulando salvamento.")
        return None
    
    try:
        collection = db["imagens_editadas"]
        
        documento = {
            "prompt_usado": edicao_data.get("prompt_usado"),
            "strength": edicao_data.get("strength"),
            "modelo": edicao_data.get("modelo"),
            "imagens_editadas": edicao_data.get("imagens_editadas", []),
            "status": edicao_data.get("status", "unknown"),
            "erro": edicao_data.get("error"),
            "criado_em": datetime.utcnow()
        }
        
        resultado = collection.insert_one(documento)
        print(f"✅ Imagem editada salva no MongoDB: {resultado.inserted_id}")
        return str(resultado.inserted_id)
    
    except Exception as e:
        print(f"⚠️ Erro ao salvar imagem editada no MongoDB: {str(e)}")
        return None
