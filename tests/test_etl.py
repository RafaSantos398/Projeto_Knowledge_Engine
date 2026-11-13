"""Testes de integridade dos dados e das transformações, sem calcular as respostas."""

import csv
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

import etl
from baixar_dados import DESTINO


def linha(**alteracoes):
    registro = dict(zip(etl.CAMPOS, (
        "2002-05-31", "France", "Senegal", "1", "42", "0", "1",
        "FIFA World Cup", "No", "Lose",
    )))
    registro.update(alteracoes)
    return registro


class TesteConversao(unittest.TestCase):
    def test_campos_e_nomes(self):
        partida = etl.converter_linha(linha(), 100)
        self.assertEqual((partida.selecao_a, partida.selecao_b), ("franca", "senegal"))
        self.assertEqual(partida.resultado_a, "derrota")
        self.assertEqual(partida.original_a, "France")

    def test_servia_montenegro_nao_se_confunde_com_servia(self):
        self.assertEqual(etl.normalizar_nome("Serbia", 2006), "servia_e_montenegro")
        self.assertEqual(etl.normalizar_nome("Serbia", 2018), "servia")

    def test_penaltis_preservam_resultado_mesmo_com_placar_igual(self):
        p = etl.converter_linha(linha(home_team_score="1", away_team_score="1",
                                     shoot_out="Yes", home_team_result="Lose"), 2)
        self.assertEqual((p.penaltis, p.resultado_a), ("sim", "derrota"))

    def test_entrada_incoerente_falha_com_numero_da_linha(self):
        casos = [
            {"home_team_fifa_rank": ""}, {"away_team_fifa_rank": "0"},
            {"home_team_score": "-1"}, {"away_team_score": "1.5"},
            {"home_team_result": "Win"}, {"shoot_out": "maybe"},
            {"shoot_out": "Yes"}, {"home_team": "Inventada"},
            {"date": "2002-05-30"}, {"date": "2002-02-31"},
            {"away_team": "France"},
        ]
        for alteracao in casos:
            with self.subTest(alteracao=alteracao):
                with self.assertRaisesRegex(ValueError, "Linha 55"):
                    etl.converter_linha(linha(**alteracao), 55)

    def test_referencia_permanece_fixa_e_independe_da_ordem(self):
        p = etl.converter_linha(linha(), 2)
        posterior = replace(p, data=date(2002, 6, 6), rank_a=9, linha=3)
        referencias = etl.extrair_referencias([posterior, p])
        self.assertEqual(referencias[2002, "franca"], (1, date(2002, 5, 31), 2))

    def test_duplicata_invertida_e_detectada(self):
        p = etl.converter_linha(linha(), 2)
        invertida = replace(p, selecao_a=p.selecao_b, selecao_b=p.selecao_a, linha=3)
        with self.assertRaisesRegex(ValueError, "duplicada"):
            etl.validar_recorte([p, invertida])

    def test_recorte_incompleto_e_rejeitado(self):
        with self.assertRaisesRegex(ValueError, "64 jogos"):
            etl.validar_recorte([etl.converter_linha(linha(), 2)])


class TesteBaseReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.partidas, cls.total = etl.carregar_partidas(DESTINO)

    def test_320_jogos_160_referencias_16_penaltis(self):
        self.assertEqual((self.total, len(self.partidas)), (23921, 320))
        self.assertEqual(len(etl.extrair_referencias(self.partidas)), 160)
        self.assertEqual(sum(p.penaltis == "sim" for p in self.partidas), 16)

    def test_russia_2018_usa_70_em_vez_do_rank_atualizado(self):
        referencias = etl.extrair_referencias(self.partidas)
        self.assertEqual(referencias[2018, "russia"][0], 70)
        partida = next(p for p in self.partidas if p.selecao_a == "russia"
                       and p.selecao_b == "espanha" and p.edicao == 2018)
        self.assertEqual(partida.rank_a, 49)

    def test_geracao_reproduzivel_e_rastreavel(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            etl.executar(DESTINO, raiz)
            antes = {p.relative_to(raiz): p.read_bytes() for p in raiz.rglob("*") if p.is_file()}
            etl.executar(DESTINO, raiz)
            depois = {p.relative_to(raiz): p.read_bytes() for p in raiz.rglob("*") if p.is_file()}
            self.assertEqual(antes, depois)
            texto = (raiz / "base.pl").read_text(encoding="utf-8")
            self.assertEqual(sum(l.startswith("jogo(") for l in texto.splitlines()), 320)
            with (raiz / "docs" / "rastreabilidade.csv").open(encoding="utf-8", newline="") as f:
                rastros = list(csv.DictReader(f))
            with DESTINO.open(encoding="utf-8-sig", newline="") as f:
                fonte = list(csv.DictReader(f))
            for rastro in rastros:
                original = fonte[int(rastro["linha_csv"]) - 2]
                self.assertEqual(original["date"], rastro["data"])
                self.assertEqual(original["home_team"], rastro["nome_original_a"])

    def test_fonte_modificada_e_rejeitada_antes_de_gerar(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            arquivo = raiz / "adulterado.csv"
            arquivo.write_bytes(DESTINO.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                etl.executar(arquivo, raiz / "saida")
            self.assertFalse((raiz / "saida").exists())


if __name__ == "__main__":
    unittest.main()
