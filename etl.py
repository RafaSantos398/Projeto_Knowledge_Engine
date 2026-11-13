"""Valida o CSV e gera fatos e consultas; as respostas são calculadas em Prolog."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from baixar_dados import DESTINO, SHA256

RAIZ = Path(__file__).resolve().parent
EDICOES = (2002, 2006, 2010, 2014, 2018)
CAMPOS = (
    "date", "home_team", "away_team", "home_team_fifa_rank",
    "away_team_fifa_rank", "home_team_score", "away_team_score",
    "tournament", "shoot_out", "home_team_result",
)
PERIODOS = {
    2002: ("2002-05-31", "2002-06-30"),
    2006: ("2006-06-09", "2006-07-09"),
    2010: ("2010-06-11", "2010-07-11"),
    2014: ("2014-06-12", "2014-07-13"),
    2018: ("2018-06-14", "2018-07-15"),
}
# Cada nome original é preservado na rastreabilidade. Sérvia 2006 é um caso histórico.
NOMES = {
    "Algeria": "argelia", "Angola": "angola", "Argentina": "argentina",
    "Australia": "australia", "Belgium": "belgica",
    "Bosnia and Herzegovina": "bosnia_e_herzegovina", "Brazil": "brasil",
    "Cameroon": "camaroes", "Chile": "chile", "China PR": "china",
    "Colombia": "colombia", "Costa Rica": "costa_rica", "Croatia": "croacia",
    "Czech Republic": "republica_tcheca", "Côte d'Ivoire": "costa_do_marfim",
    "Denmark": "dinamarca", "Ecuador": "equador", "Egypt": "egito",
    "England": "inglaterra", "France": "franca", "Germany": "alemanha",
    "Ghana": "gana", "Greece": "grecia", "Honduras": "honduras",
    "IR Iran": "ira", "Iceland": "islandia", "Italy": "italia",
    "Japan": "japao", "Korea DPR": "coreia_do_norte",
    "Korea Republic": "coreia_do_sul", "Mexico": "mexico", "Morocco": "marrocos",
    "Netherlands": "holanda", "New Zealand": "nova_zelandia", "Nigeria": "nigeria",
    "Panama": "panama", "Paraguay": "paraguai", "Peru": "peru", "Poland": "polonia",
    "Portugal": "portugal", "Republic of Ireland": "irlanda", "Russia": "russia",
    "Saudi Arabia": "arabia_saudita", "Senegal": "senegal", "Serbia": "servia",
    "Slovakia": "eslovaquia", "Slovenia": "eslovenia", "South Africa": "africa_do_sul",
    "Spain": "espanha", "Sweden": "suecia", "Switzerland": "suica", "Togo": "togo",
    "Trinidad and Tobago": "trinidad_e_tobago", "Tunisia": "tunisia",
    "Turkey": "turquia", "USA": "estados_unidos", "Ukraine": "ucrania",
    "Uruguay": "uruguai",
}


@dataclass(frozen=True)
class Partida:
    linha: int
    data: date
    selecao_a: str
    selecao_b: str
    rank_a: int
    rank_b: int
    gols_a: int
    gols_b: int
    penaltis: str
    resultado_a: str
    original_a: str
    original_b: str

    @property
    def edicao(self):
        return self.data.year


def normalizar_nome(nome, edicao):
    if nome == "Serbia" and edicao == 2006:
        return "servia_e_montenegro"
    try:
        return NOMES[nome]
    except KeyError as erro:
        raise ValueError(f"Seleção desconhecida: {nome!r}") from erro


def inteiro(valor, campo, minimo):
    # int('1.0') falha propositalmente: o esquema exige números inteiros.
    numero = int(valor)
    if numero < minimo:
        raise ValueError(f"{campo} deve ser >= {minimo}: {valor!r}")
    return numero


def converter_linha(registro, linha):
    """Valida uma linha selecionada, inclusive a coerência entre placar e resultado."""
    try:
        for campo in CAMPOS:
            if registro.get(campo) is None or not registro[campo].strip():
                raise ValueError(f"campo ausente ou vazio: {campo}")
        dia = date.fromisoformat(registro["date"])
        if dia.year not in EDICOES or registro["tournament"] != "FIFA World Cup":
            raise ValueError("linha fora do recorte")
        inicio, fim = PERIODOS[dia.year]
        if not inicio <= dia.isoformat() <= fim:
            raise ValueError("data fora do período da Copa")
        original_a, original_b = registro["home_team"], registro["away_team"]
        a, b = (normalizar_nome(n, dia.year) for n in (original_a, original_b))
        if a == b:
            raise ValueError("seleção não pode jogar contra si mesma")
        ra = inteiro(registro["home_team_fifa_rank"], "ranking A", 1)
        rb = inteiro(registro["away_team_fifa_rank"], "ranking B", 1)
        ga = inteiro(registro["home_team_score"], "gols A", 0)
        gb = inteiro(registro["away_team_score"], "gols B", 0)
        resultado = {"Win": "vitoria", "Lose": "derrota", "Draw": "empate"}
        resultado_a = resultado[registro["home_team_result"]]
        penaltis = {"Yes": "sim", "No": "nao"}[registro["shoot_out"]]
        if penaltis == "sim":
            if ga != gb or resultado_a == "empate":
                raise ValueError("pênaltis exigem placar empatado e vencedor informado")
        else:
            esperado = "vitoria" if ga > gb else "derrota" if ga < gb else "empate"
            if resultado_a != esperado:
                raise ValueError("resultado incompatível com o placar")
        return Partida(linha, dia, a, b, ra, rb, ga, gb, penaltis,
                       resultado_a, original_a, original_b)
    except (ValueError, KeyError) as erro:
        raise ValueError(f"Linha {linha}: {erro}") from erro


def validar_recorte(partidas):
    vistos = set()
    contagens = Counter()
    selecoes = defaultdict(set)
    for p in partidas:
        chave = (p.data, tuple(sorted((p.selecao_a, p.selecao_b))))
        if chave in vistos:
            raise ValueError(f"Partida duplicada: {chave}")
        vistos.add(chave)
        contagens[p.edicao] += 1
        selecoes[p.edicao].update((p.selecao_a, p.selecao_b))
    for edicao in EDICOES:
        if contagens[edicao] != 64 or len(selecoes[edicao]) != 32:
            raise ValueError(
                f"Copa {edicao}: esperados 64 jogos e 32 seleções; "
                f"encontrados {contagens[edicao]} e {len(selecoes[edicao])}."
            )


def carregar_partidas(caminho):
    partidas = []
    total_linhas = 0
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if len(leitor.fieldnames or []) != len(set(leitor.fieldnames or [])):
            raise ValueError("Cabeçalho contém campos duplicados.")
        faltantes = set(CAMPOS) - set(leitor.fieldnames or [])
        if faltantes:
            raise ValueError(f"Colunas ausentes: {sorted(faltantes)}")
        for registro in leitor:
            total_linhas += 1
            if registro["tournament"] != "FIFA World Cup":
                continue
            try:
                ano = date.fromisoformat(registro["date"]).year
            except (ValueError, TypeError) as erro:
                raise ValueError(f"Data inválida na linha {leitor.line_num}.") from erro
            if ano in EDICOES:
                partidas.append(converter_linha(registro, leitor.line_num))
    partidas.sort(key=lambda p: (p.data, p.selecao_a, p.selecao_b))
    validar_recorte(partidas)
    return partidas, total_linhas


def extrair_referencias(partidas):
    """Primeiro registro cronológico por edição/seleção; não atualiza durante a Copa."""
    referencias = {}
    for p in sorted(partidas, key=lambda item: (item.data, item.linha)):
        for selecao, rank in ((p.selecao_a, p.rank_a), (p.selecao_b, p.rank_b)):
            referencias.setdefault((p.edicao, selecao), (rank, p.data, p.linha))
    return referencias


def termo_data(dia):
    return f"data({dia.year},{dia.month},{dia.day})"


def gerar_base(partidas, referencias):
    linhas = [
        "% Gerado por etl.py. Não editar manualmente.",
        f"% SHA-256 do CSV: {SHA256}",
        "% ranking_pre_copa = ranking de estreia no CSV, uma aproximação documentada.",
        ":- encoding(utf8).", "",
        "% jogo(Data,A,B,RankAOriginal,RankBOriginal,GolsA,GolsB,Torneio,Penaltis,ResultadoA).",
    ]
    for p in partidas:
        linhas.append(
            f"jogo({termo_data(p.data)},{p.selecao_a},{p.selecao_b},"
            f"{p.rank_a},{p.rank_b},{p.gols_a},{p.gols_b},fifa_world_cup,"
            f"{p.penaltis},{p.resultado_a})."
        )
    linhas.extend(["", "% Referência fixa: uma posição por seleção e edição."])
    for (edicao, selecao), (rank, _, _) in sorted(referencias.items()):
        linhas.append(f"ranking_pre_copa({edicao},{selecao},{rank}).")
    linhas.extend(["", "% Data da estreia e linha no CSV original (cabeçalho = linha 1)."])
    for (edicao, selecao), (_, dia, linha) in sorted(referencias.items()):
        linhas.append(f"referencia_ranking({edicao},{selecao},{termo_data(dia)},{linha}).")
    return "\n".join(linhas) + "\n"


CONSULTAS = """% Gerado por etl.py. Execute consultas no terminal Prolog, não nesta área.
:- encoding(utf8).
:- ensure_loaded('regras.pl').
:- ensure_loaded('relatorio.pl').

% P1: Quais foram as dez maiores zebras por diferença de posições?
% Composição de regras, cálculo, coleta e ordenação com desempate reproduzível.
% ?- pergunta_1(Lista).
pergunta_1(Lista) :- top_zebras(10, Lista).

% P2: Qual Copa teve a maior proporção de zebras?
% Agrupamento por edição, contagem, proporção e ordenação.
% ?- pergunta_2(Tabela, Lideres).
pergunta_2(Tabela, Lideres) :-
    resumo_copas(Tabela),
    copas_mais_imprevisiveis(Lideres).

% P3: Quais seleções tiveram a maior taxa de vitória como azarãs?
% Agrupamento por seleção, contagem condicional e mínimo de três jogos.
% ?- pergunta_3(Lista).
pergunta_3(Lista) :- desempenho_azaroes(3, Lista).

% ?- mostrar_resultados.
% ?- exportar_resultados.  % grava docs/resultados.md
"""


def gravar_csv(caminho, cabecalho, registros):
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(cabecalho)
        escritor.writerows(registros)


def gerar_programa_swish(base):
    """Junta o mesmo programa em um arquivo, sem operações de disco, para o SWISH."""
    regras = (RAIZ / "regras.pl").read_text(encoding="utf-8")
    regras = regras.replace(":- ensure_loaded('base.pl').\n", "")
    regras = regras.replace(":- dynamic jogo/10, ranking_pre_copa/3, referencia_ranking/4.\n", "")
    consultas = "\n".join(l for l in CONSULTAS.splitlines()
                          if not l.startswith(":- ensure_loaded") and "exportar_resultados" not in l)
    relatorio = (RAIZ / "relatorio.pl").read_text(encoding="utf-8")
    relatorio = relatorio.split("% O destino padrão")[0]
    relatorio = relatorio.replace(":- use_module(library(filesex)).\n", "")
    return ("% Arquivo único para colar na área Program do SWISH.\n"
            "% Consultas: pergunta_1(L). pergunta_2(T,L). pergunta_3(L).\n"
            "% Gerado pelo ETL a partir dos mesmos fatos e regras do projeto.\n\n"
            + base + "\n" + regras + "\n" + consultas + "\n" + relatorio)


def executar(entrada=DESTINO, saida=RAIZ):
    entrada, saida = Path(entrada), Path(saida)
    digest = hashlib.sha256(entrada.read_bytes()).hexdigest()
    if digest != SHA256:
        raise ValueError("SHA-256 diferente da versão estudada. Consulte data/fonte.json.")
    partidas, total_linhas = carregar_partidas(entrada)
    referencias = extrair_referencias(partidas)
    docs = saida / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    base = gerar_base(partidas, referencias)
    (saida / "base.pl").write_text(base, encoding="utf-8", newline="\n")
    (saida / "consultas.pl").write_text(CONSULTAS, encoding="utf-8", newline="\n")
    (saida / "projeto_swish.pl").write_text(gerar_programa_swish(base), encoding="utf-8", newline="\n")
    gravar_csv(docs / "rastreabilidade.csv",
               ("linha_csv", "data", "edicao", "selecao_a", "selecao_b", "nome_original_a", "nome_original_b"),
               ((p.linha, p.data.isoformat(), p.edicao, p.selecao_a, p.selecao_b,
                 p.original_a, p.original_b) for p in partidas))
    gravar_csv(docs / "referencias_ranking.csv",
               ("edicao", "selecao", "ranking_estreia_csv", "data_estreia", "linha_csv"),
               ((e, s, r, d.isoformat(), l) for (e, s), (r, d, l) in sorted(referencias.items())))
    variacoes = []
    for p in partidas:
        for selecao, rank in ((p.selecao_a, p.rank_a), (p.selecao_b, p.rank_b)):
            fixo = referencias[p.edicao, selecao][0]
            if rank != fixo:
                variacoes.append({"linha_csv": p.linha, "data": p.data.isoformat(),
                                  "edicao": p.edicao, "selecao": selecao,
                                  "ranking_no_jogo": rank, "referencia_fixa": fixo})
    relatorio = {
        "sha256": digest, "linhas_na_fonte": total_linhas,
        "campos_selecionados": list(CAMPOS), "total_partidas": len(partidas),
        "partidas_por_copa": dict(sorted(Counter(p.edicao for p in partidas).items())),
        "selecoes_por_copa": {e: len({s for ano, s in referencias if ano == e}) for e in EDICOES},
        "total_referencias": len(referencias),
        "decisoes_por_penaltis": sum(p.penaltis == "sim" for p in partidas),
        "duplicatas": 0, "campos_selecionados_vazios": 0,
        "politica_ranking": "primeiro_registro_csv_por_selecao_e_edicao_sem_correcao_externa",
        "validacao_historica_completa": False,
        "ocorrencias_com_ranking_diferente_da_estreia": variacoes,
    }
    (docs / "validacao_automatica.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=DESTINO)
    parser.add_argument("--saida", type=Path, default=RAIZ)
    args = parser.parse_args()
    try:
        resumo = executar(args.entrada, args.saida)
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Erro no ETL: {erro}\n")
    print(f"Gerados {resumo['total_partidas']} jogos e {resumo['total_referencias']} referências.")
    print("Base: base.pl | Consultas: consultas.pl | Verificações: docs/validacao_automatica.json")
    print("Atenção: rankings de estreia do CSV são uma aproximação; consulte docs/validacao.md.")


if __name__ == "__main__":
    main()
