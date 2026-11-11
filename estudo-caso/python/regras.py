"""Regras do SIS Eventos convertidas do Power Fx para Python.

Cada função reproduz uma fórmula de estudo-caso/formulas/, sem corrigir
comportamentos do sistema antigo. Dinheiro usa Decimal.

Convenções para imitar o Power Fx:
- campo vazio no CSV  -> None (equivale a Blank());
- em contas, None vale 0 (como Blank() em operações aritméticas);
- Round(x; 2) arredonda "para longe do zero" (ROUND_HALF_UP no Decimal).
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"

# Nomes dos campos, iguais aos das fórmulas.
CAMPOS_NUMERICOS = {
    "ID", "ID_EVENTO", "QTD de Pessoas", "QTD de Diárias", "ID_Diaria",
    "Valor diária - Outro Cargo", "Valor em U$ diária internacional",
    "Cotação Dolar/Real", "ValorConvertido", "Valor Inscrição",
    "InscricaoConvertida", "Valor Custo Complementar", "Valor Seguro Viagem",
    "Passagem individual", "Realizado", "Valor",
}


# ---------------------------------------------------------------------------
# Leitura dos dados
# ---------------------------------------------------------------------------

def _ler_csv(nome, pasta=PASTA_DADOS):
    with open(Path(pasta) / nome, encoding="utf-8", newline="") as f:
        linhas = []
        for linha in csv.DictReader(f):
            registro = {}
            for campo, valor in linha.items():
                if campo == "Excluido":
                    registro[campo] = valor  # "" ou "*"
                elif valor == "":
                    registro[campo] = None  # Blank()
                elif campo in CAMPOS_NUMERICOS:
                    registro[campo] = Decimal(valor)
                else:
                    registro[campo] = valor
            linhas.append(registro)
        return linhas


def carregar_eventos(pasta=PASTA_DADOS):
    """TB_EVENTOS. DT_Inicio vira o ano (int); a fórmula só usa Year()."""
    eventos = _ler_csv("eventos.csv", pasta)
    for e in eventos:
        e["ID"] = int(e["ID"])
        e["ano"] = int(e["DT_Inicio"][:4])  # DT_Inicio no formato AAAA-MM-DD
    return eventos


def carregar_custos(pasta=PASTA_DADOS):
    """TB_PREVISAO_CUSTO_EVENTOS."""
    return _ler_csv("custos.csv", pasta)


def carregar_diarias(pasta=PASTA_DADOS):
    """TB_DIARIAS_NACIONAIS."""
    return _ler_csv("diarias.csv", pasta)


# ---------------------------------------------------------------------------
# Auxiliares que imitam o Power Fx
# ---------------------------------------------------------------------------

def _n(valor):
    """Blank() em conta vale 0."""
    return Decimal(0) if valor is None else valor


def _round2(valor):
    """Round(x; 2) do Power Fx."""
    return _n(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _lookup_valor_diaria(diarias, id_diaria):
    """LookUp(tabela; ID = id_diaria; Valor). Sem resultado -> None."""
    for d in diarias:
        if id_diaria is not None and d["ID"] == id_diaria:
            return d["Valor"]
    return None


def formatar_reais(valor):
    """Formato "[$-pt-BR]#.##0,00" com o prefixo "R$ ".

    Text(Blank(); ...) devolve texto vazio, então None vira só "R$ ".
    """
    if valor is None:
        return "R$ "
    v = _n(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    texto = f"{v:,.2f}"  # 19,450.00
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


# ---------------------------------------------------------------------------
# Regra 01 - registros excluídos / eventos por ano (Gallery2_6.Items)
# ---------------------------------------------------------------------------

STATUS_REGRA_01 = {
    "EM_ABERTO": "Em Aberto",
    "EM_ANALISE": "Em Análise",
    "NAO_APROVADO": "Não Aprovado",
    "APROVADO": "Aprovado",
    "CANCELADO": "Cancelado",
    "APROVADO_AJUSTE": "Aprovado para ajustes",
}


def regra01_eventos_por_ano(eventos):
    """Lista de anos (do maior para o menor) com as contagens por status.

    Igual à fórmula: os anos vêm de TODOS os eventos (inclusive excluídos),
    mas as contagens usam só os não excluídos; anos com QTD_EVENTOS = 0 somem.
    """
    nao_excluidos = [e for e in eventos if e["Excluido"] != "*"]
    anos_distintos = []
    for e in eventos:  # Distinct mantém a ordem de primeira aparição
        if e["ano"] not in anos_distintos:
            anos_distintos.append(e["ano"])

    resultado = []
    for ano in anos_distintos:
        linha = {
            "Value": ano,
            "QTD_EVENTOS": sum(1 for e in nao_excluidos if e["ano"] == ano),
        }
        for coluna, status in STATUS_REGRA_01.items():
            linha[coluna] = sum(
                1 for e in nao_excluidos
                if e["ano"] == ano and e["Status de participação"] == status
            )
        if linha["QTD_EVENTOS"] != 0:
            resultado.append(linha)
    resultado.sort(key=lambda linha: linha["Value"], reverse=True)
    return resultado


# ---------------------------------------------------------------------------
# Regra 02 - valor de cada linha de custo (TextCanvas7_96.Text)
# ---------------------------------------------------------------------------

def regra02_valor_linha(custo, diarias):
    """Valor (Decimal) da linha de custo, ou None se nenhum caso se aplica.

    Testa os casos na mesma ordem do Switch original. Não olha o campo
    Excluido da linha nem o da diária (a fórmula original também não).
    """
    tipo = custo["Tipo de Custo"]
    pessoas = _n(custo["QTD de Pessoas"])
    qtd_diarias = _n(custo["QTD de Diárias"])

    if tipo == "Seguro Viagem":
        return _n(custo["Valor Seguro Viagem"]) * pessoas
    if tipo == "Diária" and custo["Valor em U$ diária internacional"] is not None:
        return custo["ValorConvertido"]
    if tipo == "Passagem":
        return pessoas * _n(custo["Passagem individual"])
    if tipo == "Diária" and custo["ID_Diaria"] is None:
        return qtd_diarias * _n(custo["Valor diária - Outro Cargo"]) * pessoas
    if tipo == "Diária" and custo["ID_Diaria"] is not None:
        return qtd_diarias * _n(_lookup_valor_diaria(diarias, custo["ID_Diaria"]))
    if tipo == "Inscrição":
        return custo["InscricaoConvertida"]
    if custo["Valor Custo Complementar"] is not None:
        return custo["Valor Custo Complementar"]
    return None


def regra02_texto(custo, diarias):
    """Texto como o app mostra: "R$ 1.234,56"."""
    return formatar_reais(regra02_valor_linha(custo, diarias))


# ---------------------------------------------------------------------------
# Regras 03 e 04 - totais do ano (ButtonCanvas6_3 / ButtonCanvas6_4)
# ---------------------------------------------------------------------------

def _eventos_aprovados_do_ano(eventos, ano):
    return [
        e for e in eventos
        if e["Status de participação"] == "Aprovado"
        and e["ano"] == ano
        and e["Excluido"] != "*"
    ]


def _total_previsto_da_linha(c, diarias_validas):
    """As sete partes da fórmula 03, cada uma com Round(...; 2).

    Soma todos os campos da linha, sem olhar o Tipo de Custo.
    """
    pessoas = _n(c["QTD de Pessoas"])
    qtd_diarias = _n(c["QTD de Diárias"])
    cotacao = _n(c["Cotação Dolar/Real"])

    outro_cargo = _round2(qtd_diarias * _n(c["Valor diária - Outro Cargo"]) * pessoas)
    nacional = _round2(
        qtd_diarias * _n(_lookup_valor_diaria(diarias_validas, c["ID_Diaria"])) * pessoas
    )
    internacional = _round2(
        (cotacao * _n(c["Valor em U$ diária internacional"])) * (qtd_diarias * pessoas)
    )
    if c["Moeda  - Inscrição"] == "US$":
        inscricao = _round2(cotacao * _n(c["Valor Inscrição"]))
    else:
        inscricao = _round2(c["Valor Inscrição"])
    complementar = _round2(c["Valor Custo Complementar"])
    seguro = _round2(_n(c["Valor Seguro Viagem"]) * pessoas)
    passagem = _round2(_n(c["Passagem individual"]) * pessoas)

    return outro_cargo + nacional + internacional + inscricao + complementar + seguro + passagem


def regra03_total_previsto(ano, eventos, custos, diarias):
    """Total previsto (Decimal) dos eventos aprovados e não excluídos do ano."""
    diarias_validas = [d for d in diarias if d["Excluido"] != "*"]
    total = Decimal(0)
    for evento in _eventos_aprovados_do_ano(eventos, ano):
        linhas = [
            c for c in custos
            if c["ID_EVENTO"] == evento["ID"] and c["Excluido"] != "*"
        ]
        total += sum((_total_previsto_da_linha(c, diarias_validas) for c in linhas), Decimal(0))
    return total


def regra03_texto(ano, eventos, custos, diarias):
    return formatar_reais(regra03_total_previsto(ano, eventos, custos, diarias))


def regra04_total_realizado(ano, eventos, custos):
    """Soma de Realizado das linhas não excluídas dos eventos aprovados do ano.

    Campos Realizado vazios são ignorados (Sum ignora Blank()).
    """
    ids = {e["ID"] for e in _eventos_aprovados_do_ano(eventos, ano)}
    return sum(
        (c["Realizado"] for c in custos
         if c["Excluido"] != "*" and c["ID_EVENTO"] in ids and c["Realizado"] is not None),
        Decimal(0),
    )


def regra04_texto(ano, eventos, custos):
    # Coalesce("R$ " & Text(...); "-"): o primeiro argumento nunca é vazio,
    # porque sempre começa com "R$ ". Por isso o "-" não aparece.
    return formatar_reais(regra04_total_realizado(ano, eventos, custos))
