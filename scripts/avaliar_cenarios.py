"""
Avaliação técnica dos cenários simulados S1–S3 (Seção de Protocolo de avaliação do artigo).

Executa a geração N vezes por cenário, sem passar pela API HTTP nem exigir login,
e grava um CSV com uma linha por provedor/execução: sucesso, tempo e conformidade
da legenda. No final, imprime o resumo por cenário e provedor, no formato da
tabela de validação técnica (C1, C2 e C5).

A publicação (C3) NÃO é feita aqui, para não publicar várias vezes na conta;
faça-a pela API/interface e registre o resultado (a coleção "publicacoes" do
MongoDB guarda cada tentativa).

Uso (na raiz do projeto):
    python -m scripts.avaliar_cenarios --repeticoes 5
    python -m scripts.avaliar_cenarios --repeticoes 3 --somente-texto
    python -m scripts.avaliar_cenarios --cenarios S1 S2 --saida resultados.csv

Atenção: cada execução consome créditos dos provedores configurados.
"""
import argparse
import csv
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.multi_model_service import gerar_conteudo_multi_modelo  # noqa: E402

CENARIOS = {
    "S1": {
        "tema": "lançamento da coleção de verão de uma loja de roupas",
        "objetivo": "vender produto",
        "publico": "mulheres de 20 a 35 anos",
        "tom": "descontraído",
    },
    "S2": {
        "tema": "dica de alimentação saudável de uma nutricionista",
        "objetivo": "educar o público",
        "publico": "adultos que buscam hábitos saudáveis",
        "tom": "profissional",
    },
    "S3": {
        "tema": "cafeteria local",
        "objetivo": "fortalecer a marca",
        "publico": "moradores e estudantes da cidade",
        "tom": "acolhedor",
    },
}

CAMPOS = [
    "cenario", "execucao", "tipo", "provedor", "modelo", "status", "tempo_s",
    "caracteres", "emojis", "hashtags", "ctas_detectadas", "conforme",
    "url_publica", "legenda", "erro",
]


def _linhas(cenario: str, execucao: int, resultado: dict):
    for item in resultado["imagens"] + resultado["imagens_falhas"]:
        yield {
            "cenario": cenario, "execucao": execucao, "tipo": "imagem",
            "provedor": item.get("provedor"), "modelo": item.get("modelo"),
            "status": item.get("status"), "tempo_s": item.get("tempo_s"),
            "url_publica": item.get("url_publica"), "erro": item.get("error"),
        }
    for item in resultado["legendas"] + resultado["legendas_falhas"]:
        conf = item.get("conformidade") or {}
        yield {
            "cenario": cenario, "execucao": execucao, "tipo": "legenda",
            "provedor": item.get("provedor"), "modelo": item.get("modelo"),
            "status": item.get("status"), "tempo_s": item.get("tempo_s"),
            "caracteres": conf.get("caracteres"), "emojis": conf.get("emojis"),
            "hashtags": conf.get("hashtags"), "ctas_detectadas": conf.get("ctas_detectadas"),
            "conforme": conf.get("conforme"), "legenda": item.get("legenda"),
            "erro": item.get("error"),
        }


def _resumo(linhas):
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[(linha["cenario"], linha["tipo"], linha["provedor"])].append(linha)

    print("\nResumo por cenário e provedor")
    print(f"{'Cen.':<5}{'Tipo':<9}{'Provedor':<16}{'Sucesso':>10}{'Tempo médio (s)':>17}{'DP (s)':>9}{'Conformes':>11}")
    for (cenario, tipo, provedor), itens in sorted(grupos.items()):
        sucessos = [i for i in itens if i["status"] == "success"]
        tempos = [float(i["tempo_s"]) for i in sucessos if i["tempo_s"] is not None]
        media = statistics.mean(tempos) if tempos else float("nan")
        dp = statistics.stdev(tempos) if len(tempos) > 1 else 0.0
        conformes = (
            f"{sum(1 for i in sucessos if i.get('conforme'))}/{len(sucessos)}"
            if tipo == "legenda" else "-"
        )
        print(f"{cenario:<5}{tipo:<9}{provedor:<16}{len(sucessos):>5}/{len(itens):<4}"
              f"{media:>17.2f}{dp:>9.2f}{conformes:>11}")


def main():
    parser = argparse.ArgumentParser(description="Avaliação técnica dos cenários S1–S3.")
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--cenarios", nargs="+", default=list(CENARIOS), choices=list(CENARIOS))
    parser.add_argument("--somente-texto", action="store_true", help="Gera apenas legendas (sem custo de imagem)")
    parser.add_argument("--saida", default=f"avaliacao_{datetime.now():%Y%m%d_%H%M%S}.csv")
    args = parser.parse_args()

    linhas = []
    for cenario in args.cenarios:
        for execucao in range(1, args.repeticoes + 1):
            params = {
                **CENARIOS[cenario],
                "tipo": "texto" if args.somente_texto else "imagem",
                "rede_alvo": "Instagram",
                "formato": "post de feed com imagem única",
            }
            print(f"▶ {cenario} – execução {execucao}/{args.repeticoes}...", flush=True)
            resultado = gerar_conteudo_multi_modelo(params)
            novas = list(_linhas(cenario, execucao, resultado))
            linhas.extend(novas)
            for linha in novas:
                marca = "✓" if linha["status"] == "success" else "✗"
                print(f"   {marca} {linha['tipo']:<8}{linha['provedor']:<16}{linha['tempo_s']} s"
                      + (f"  conforme={linha['conforme']}" if linha["tipo"] == "legenda" else "")
                      + (f"  erro={linha['erro']}" if linha["erro"] else ""))

    with open(args.saida, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, delimiter=";")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({campo: linha.get(campo) for campo in CAMPOS})

    _resumo(linhas)
    print(f"\nCSV salvo em: {args.saida}")


if __name__ == "__main__":
    main()
