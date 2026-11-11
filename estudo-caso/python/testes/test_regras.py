"""Compara as regras convertidas com os resultados do sistema atual.

Os valores esperados vêm só de estudo-caso/resultados_esperados.csv.
Nenhum valor esperado é escrito à mão aqui.
"""

import csv
import sys
from decimal import Decimal
from pathlib import Path

import pytest

PASTA_PYTHON = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA_PYTHON))

import regras  # noqa: E402

ARQUIVO_ESPERADOS = PASTA_PYTHON.parent / "resultados_esperados.csv"

# Rótulo usado na coluna "caso" da regra 01 -> coluna criada pela fórmula 01.
COLUNA_REGRA_01 = {
    "Total": "QTD_EVENTOS",
    "Em Aberto": "EM_ABERTO",
    "Em Análise": "EM_ANALISE",
    "Não Aprovado": "NAO_APROVADO",
    "Aprovado": "APROVADO",
    "Cancelado": "CANCELADO",
    "Aprovado para ajustes": "APROVADO_AJUSTE",
}


def _esperados(regra):
    with open(ARQUIVO_ESPERADOS, encoding="utf-8", newline="") as f:
        return [linha for linha in csv.DictReader(f) if linha["regra"] == regra]


def _ids(linhas):
    return [linha["caso"] for linha in linhas]


@pytest.fixture(scope="module")
def dados():
    return {
        "eventos": regras.carregar_eventos(),
        "custos": regras.carregar_custos(),
        "diarias": regras.carregar_diarias(),
    }


def _ano(caso):
    # "ano 2026" ou "ano 2026 - Em Aberto"
    return int(caso.split()[1])


# --- Regra 01 ---------------------------------------------------------------

ESPERADOS_01 = _esperados("01")


@pytest.mark.parametrize("linha", ESPERADOS_01, ids=_ids(ESPERADOS_01))
def test_regra01(linha, dados):
    ano = _ano(linha["caso"])
    rotulo = linha["caso"].split(" - ", 1)[1]
    resultado = {r["Value"]: r for r in regras.regra01_eventos_por_ano(dados["eventos"])}
    assert ano in resultado, f"ano {ano} não aparece na galeria"
    assert resultado[ano][COLUNA_REGRA_01[rotulo]] == int(linha["resultado_sistema_atual"])


def test_regra01_ordem_decrescente(dados):
    anos_esperados = []
    for linha in ESPERADOS_01:
        ano = _ano(linha["caso"])
        if ano not in anos_esperados:
            anos_esperados.append(ano)
    anos = [r["Value"] for r in regras.regra01_eventos_por_ano(dados["eventos"])]
    assert anos == sorted(anos_esperados, reverse=True)


# --- Regra 02 ---------------------------------------------------------------

ESPERADOS_02 = _esperados("02")


@pytest.mark.parametrize("linha", ESPERADOS_02, ids=_ids(ESPERADOS_02))
def test_regra02(linha, dados):
    id_custo = Decimal(linha["caso"].split()[1])
    custo = next(c for c in dados["custos"] if c["ID"] == id_custo)
    valor = regras.regra02_valor_linha(custo, dados["diarias"])
    assert valor == Decimal(linha["resultado_sistema_atual"])
    assert regras.regra02_texto(custo, dados["diarias"]) == linha["texto_na_tela"]


# --- Regra 03 ---------------------------------------------------------------

ESPERADOS_03 = _esperados("03")


@pytest.mark.parametrize("linha", ESPERADOS_03, ids=_ids(ESPERADOS_03))
def test_regra03(linha, dados):
    ano = _ano(linha["caso"])
    args = (ano, dados["eventos"], dados["custos"], dados["diarias"])
    assert regras.regra03_total_previsto(*args) == Decimal(linha["resultado_sistema_atual"])
    assert regras.regra03_texto(*args) == linha["texto_na_tela"]


# --- Regra 04 ---------------------------------------------------------------

ESPERADOS_04 = _esperados("04")


@pytest.mark.parametrize("linha", ESPERADOS_04, ids=_ids(ESPERADOS_04))
def test_regra04(linha, dados):
    ano = _ano(linha["caso"])
    args = (ano, dados["eventos"], dados["custos"])
    assert regras.regra04_total_realizado(*args) == Decimal(linha["resultado_sistema_atual"])
    assert regras.regra04_texto(*args) == linha["texto_na_tela"]
