from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError

from app.core import config
from app.schemas.entrada import Entrada
from app.utils import criptografia
from app.utils.imagem import informacoes_imagem, para_jpeg


def test_png_com_transparencia_vira_jpeg_rgb():
    buffer = BytesIO()
    Image.new("RGBA", (10, 10), (255, 0, 0, 0)).save(buffer, "PNG")
    info = informacoes_imagem(para_jpeg(buffer.getvalue()))
    assert info["formato"] == "JPEG" and info["modo"] == "RGB"


def test_conteudo_invalido_gera_erro():
    with pytest.raises(ValueError):
        para_jpeg(b"isto nao e imagem")


def test_criptografia_de_tokens(monkeypatch):
    monkeypatch.setattr(criptografia, "_fernet", None)
    cifrado = criptografia.criptografar("EAAB-token")
    assert cifrado.startswith("enc:") and "EAAB" not in cifrado
    assert criptografia.descriptografar(cifrado) == "EAAB-token"
    assert criptografia.descriptografar("token-antigo-em-texto") == "token-antigo-em-texto"
    # Chave trocada: não quebra, apenas devolve None (exige novo login)
    monkeypatch.setattr(criptografia, "_fernet", None)
    monkeypatch.setattr(config, "JWT_SECRET_KEY", "outra-chave-bem-diferente-com-mais-de-32-caracteres")
    monkeypatch.setattr(config, "TOKEN_ENCRYPTION_KEY", None)
    assert criptografia.descriptografar(cifrado) is None
    monkeypatch.setattr(criptografia, "_fernet", None)


def test_entrada_normaliza_e_valida():
    entrada = Entrada(tema="  café \n local ", tipo="IMAGEM", objetivo="vender", publico="todos", tom="leve")
    assert entrada.tema == "café local" and entrada.tipo == "imagem"
    assert entrada.rede_alvo == "Instagram"
    with pytest.raises(ValidationError):
        Entrada(tema="café", tipo="video", objetivo="vender", publico="todos", tom="leve")


def test_login_usa_scope_ou_config_id(monkeypatch):
    from urllib.parse import parse_qs, urlparse

    from app.services import auth_service

    monkeypatch.setattr(config, "META_APP_ID", "123")
    monkeypatch.setattr(config, "META_APP_SECRET", "segredo")
    monkeypatch.setattr(config, "META_LOGIN_CONFIG_ID", None)
    url, _ = auth_service.gerar_url_login()
    query = parse_qs(urlparse(url).query)
    assert "instagram_content_publish" in query["scope"][0] and "config_id" not in query
    assert "business_management" not in query["scope"][0]

    monkeypatch.setattr(config, "META_LOGIN_CONFIG_ID", "987")
    url, _ = auth_service.gerar_url_login()
    query = parse_qs(urlparse(url).query)
    assert query["config_id"] == ["987"] and "scope" not in query


def _graph_falso(respostas):
    from tests.conftest import RespostaFalsa

    def get(url, params, timeout):
        for trecho, dados in respostas.items():
            if url.endswith(trecho):
                return RespostaFalsa(200, dados)
        return RespostaFalsa(200, {"data": []})
    return get


def test_busca_pagina_no_portfolio_quando_me_accounts_vazio(monkeypatch):
    from app.services import auth_service

    monkeypatch.setattr(auth_service.requests, "get", _graph_falso({
        "me/accounts": {"data": []},
        "me/businesses": {"data": [{"id": "B1", "name": "Portfólio"}]},
        "B1/owned_pages": {"data": [{"id": "P1", "name": "Loja", "access_token": "PT",
                                      "instagram_business_account": {"id": "IG1"}}]},
        "/IG1": {"id": "IG1", "username": "loja"},
    }))
    conta = auth_service.obter_conta_instagram("UT")
    assert conta["ig_user_id"] == "IG1" and conta["instagram_username"] == "loja"
    assert conta["access_token"] == "PT"


def test_erro_informa_permissoes_quando_nao_ha_paginas(monkeypatch):
    from app.services import auth_service

    monkeypatch.setattr(auth_service.requests, "get", _graph_falso({
        "me/permissions": {"data": [{"permission": "instagram_basic", "status": "granted"},
                                    {"permission": "pages_show_list", "status": "declined"}]},
    }))
    with pytest.raises(Exception) as erro:
        auth_service.obter_conta_instagram("UT")
    assert "Nenhuma Página" in erro.value.detail and "Recusadas: pages_show_list" in erro.value.detail


class _CursorFalso(list):
    def sort(self, campo, direcao):
        return _CursorFalso(sorted(self, key=lambda d: d[campo], reverse=direcao < 0))

    def limit(self, n):
        return _CursorFalso(self[:n])


class _ColecaoFalsa:
    def __init__(self, docs):
        self.docs = docs

    def find(self, filtro):
        def casa(doc):
            for campo, valor in filtro.items():
                if isinstance(valor, dict) and "$in" in valor:
                    if doc.get(campo) not in valor["$in"]:
                        return False
                elif doc.get(campo) != valor:
                    return False
            return True
        return _CursorFalso([d for d in self.docs if casa(d)])


def test_historico_junta_publicacoes_e_filtra_usuario(monkeypatch):
    from datetime import datetime, timezone
    from app.services import database_service as db_service

    t1 = datetime(2026, 11, 18, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 11, 18, 11, tzinfo=timezone.utc)
    banco = {
        "conteudos_gerados": _ColecaoFalsa([
            {"_id": "c1", "usuario_id": "u1", "tema": "antigo", "criado_em": t1},
            {"_id": "c2", "usuario_id": "u1", "tema": "novo", "criado_em": t2},
            {"_id": "c3", "usuario_id": "outro", "tema": "de outro", "criado_em": t2},
        ]),
        "publicacoes": _ColecaoFalsa([
            {"conteudo_id": "c1", "status": "success", "permalink": "https://ig/p/1", "criado_em": t2},
        ]),
    }
    monkeypatch.setattr(db_service, "get_mongo_client", lambda: (None, banco))

    itens = db_service.listar_historico("u1")
    assert [i["tema"] for i in itens] == ["novo", "antigo"]
    assert itens[0]["publicacoes"] == []
    assert itens[1]["publicacoes"][0]["permalink"] == "https://ig/p/1"
    assert itens[1]["criado_em"].startswith("2026-11-18T10")
    assert db_service.listar_historico(None) == []
