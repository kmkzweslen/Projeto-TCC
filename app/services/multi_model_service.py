"""
Orquestração multimodelo: gera legendas e imagens com todos os provedores
configurados, em paralelo, e devolve as opções para o usuário escolher.

- Texto e imagem são gerados ao mesmo tempo (um único pool de threads).
- Cada provedor é medido (tempo_s) e isolado: a falha de um não afeta os demais.
- Há um tempo-limite global (GENERATION_TIMEOUT_S). Ao expirar, a resposta é
  devolvida com o que ficou pronto; o pool é encerrado sem esperar as threads
  pendentes (shutdown(wait=False)), para que um provedor lento não segure a
  requisição.
- Imagens são convertidas para JPEG e hospedadas publicamente (requisitos da
  Graph API). Legendas recebem a verificação de conformidade (critério C5).
"""
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Callable, Dict, List, Optional

from app.core import config
from app.services.cloud_storage_service import hospedar_imagem
from app.services.image_generators import openai_image, stability_ai
from app.services.text_generators import gemini, gpt
from app.utils.conformidade import verificar_legenda
from app.utils.prompt_engineering import (
    MENSAGEM_SISTEMA,
    construir_prompt_imagem,
    construir_prompt_legenda,
)

# (módulo do provedor, idioma do prompt de imagem)
PROVEDORES_IMAGEM = [(openai_image, "pt"), (stability_ai, "en")]
PROVEDORES_TEXTO = [gpt, gemini]


def _executar_imagem(provedor, prompt: str, hospedar: Callable[[bytes], Dict]) -> Dict:
    inicio = time.perf_counter()
    resultado = {"provedor": provedor.NOME, "modelo": provedor.modelo(), "prompt": prompt}
    try:
        conteudo = provedor.gerar_imagem(prompt)
        tempo_geracao = time.perf_counter() - inicio
        hospedagem = hospedar(conteudo)
        resultado.update(
            status="success",
            url_publica=hospedagem["public_url"],
            cloud_info=hospedagem,
            tempo_geracao_s=round(tempo_geracao, 2),
        )
    except Exception as e:  # noqa: BLE001 - qualquer falha do provedor vira resultado de erro
        resultado.update(status="error", error=str(e))
    resultado["tempo_s"] = round(time.perf_counter() - inicio, 2)
    resultado["modelo"] = provedor.modelo()
    return resultado


def _executar_legenda(provedor, prompt: str) -> Dict:
    inicio = time.perf_counter()
    resultado = {"provedor": provedor.NOME, "modelo": provedor.modelo()}
    try:
        legenda = provedor.gerar_texto(prompt, MENSAGEM_SISTEMA)
        resultado.update(
            status="success",
            legenda=legenda,
            conformidade=verificar_legenda(legenda),
        )
    except Exception as e:  # noqa: BLE001
        resultado.update(status="error", error=str(e))
    resultado["tempo_s"] = round(time.perf_counter() - inicio, 2)
    resultado["modelo"] = provedor.modelo()
    return resultado


def gerar_conteudo_multi_modelo(
    params: Dict,
    provedores_imagem: Optional[List] = None,
    provedores_texto: Optional[List] = None,
    hospedar: Callable[[bytes], Dict] = hospedar_imagem,
    timeout_s: Optional[float] = None,
) -> Dict:
    """
    Gera as opções de legenda (e de imagem, se tipo == "imagem").

    Os parâmetros opcionais permitem trocar provedores e hospedagem nos testes.
    """
    inicio = time.perf_counter()
    timeout_s = config.GENERATION_TIMEOUT_S if timeout_s is None else timeout_s
    provedores_imagem = PROVEDORES_IMAGEM if provedores_imagem is None else provedores_imagem
    provedores_texto = PROVEDORES_TEXTO if provedores_texto is None else provedores_texto

    gerar_imagens = (params.get("tipo") or "imagem").lower() == "imagem"
    imagens_ativas = [(p, idioma) for p, idioma in provedores_imagem if p.disponivel()] if gerar_imagens else []
    textos_ativos = [p for p in provedores_texto if p.disponivel()]

    if not textos_ativos:
        raise RuntimeError(
            "Nenhum provedor de texto configurado (defina OPENAI_API_KEY e/ou GEMINI_API_KEY)."
        )

    prompt_legenda = construir_prompt_legenda(params)
    tarefas = {}  # future -> (tipo, provedor)

    executor = ThreadPoolExecutor(max_workers=len(imagens_ativas) + len(textos_ativos))
    try:
        for provedor, idioma in imagens_ativas:
            prompt_img = construir_prompt_imagem(params, idioma=idioma)
            futuro = executor.submit(_executar_imagem, provedor, prompt_img, hospedar)
            tarefas[futuro] = ("imagem", provedor)
        for provedor in textos_ativos:
            futuro = executor.submit(_executar_legenda, provedor, prompt_legenda)
            tarefas[futuro] = ("legenda", provedor)

        concluidas, pendentes = wait(tarefas, timeout=timeout_s)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    imagens, legendas, imagens_falhas, legendas_falhas = [], [], [], []
    for futuro, (tipo, provedor) in tarefas.items():
        if futuro in concluidas:
            resultado = futuro.result()
        else:
            resultado = {
                "provedor": provedor.NOME,
                "modelo": provedor.modelo(),
                "status": "error",
                "error": f"Tempo-limite de {timeout_s:.0f} s excedido",
                "tempo_s": round(timeout_s, 2),
            }
        sucesso = resultado.get("status") == "success"
        if tipo == "imagem":
            (imagens if sucesso else imagens_falhas).append(resultado)
        else:
            (legendas if sucesso else legendas_falhas).append(resultado)

    return {
        "tipo": "imagem" if gerar_imagens else "texto",
        "imagens": imagens,
        "legendas": legendas,
        "imagens_falhas": imagens_falhas,
        "legendas_falhas": legendas_falhas,
        "total_combinacoes": (len(imagens) if gerar_imagens else 1) * len(legendas),
        "prompt_legenda": prompt_legenda,
        "tempo_total_s": round(time.perf_counter() - inicio, 2),
    }


def persistir_resultado(resultado: Dict, params: Dict, usuario_id: Optional[str]) -> Optional[str]:
    """Grava o conteúdo e cada opção no MongoDB. Falhas são registradas e ignoradas."""
    from app.services.database_service import (
        salvar_conteudo_completo,
        salvar_imagem_gerada,
        salvar_legenda_gerada,
    )

    try:
        base = {**params, "usuario_id": usuario_id}
        conteudo_id = salvar_conteudo_completo({**resultado, **base})
        for imagem in resultado.get("imagens", []) + resultado.get("imagens_falhas", []):
            salvar_imagem_gerada({**imagem, **base})
        for legenda in resultado.get("legendas", []) + resultado.get("legendas_falhas", []):
            salvar_legenda_gerada({**legenda, **base})
        return conteudo_id
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Erro ao salvar no MongoDB (continuando): {e}")
        return None
