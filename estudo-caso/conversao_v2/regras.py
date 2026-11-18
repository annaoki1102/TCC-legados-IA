"""Conversão para Python das 4 regras de negócio em formulas/ (Power Fx).

Convenções adotadas (semântica do Power Fx, não suposições de negócio):
- Célula vazia no CSV  -> None (equivale a Blank() no Power Fx).
- Blank em conta aritmética vale 0 (comportamento documentado do Power Fx).
- Sum() ignora valores Blank.
- Round(x; 2) do Power Fx arredonda "metade para longe do zero",
  que em Decimal é ROUND_HALF_UP.
- Excluido <> "*" : só o texto exato "*" marca exclusão (Blank não é "*").
- Dinheiro e quantidades são Decimal; IDs são int; datas são date.

Pontos ambíguos das fórmulas estão anotados em DUVIDAS.md e marcados no
código com "DUVIDA-n". O código segue a fórmula literalmente nesses pontos.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Iterable, Optional

PASTA_DADOS = Path(__file__).resolve().parent / "dados"

# ---------------------------------------------------------------------------
# Leitura dos CSV
# ---------------------------------------------------------------------------

_CAMPOS_INT = {"ID", "ID_EVENTO", "ID_Diaria"}
_CAMPOS_DATA = {"DT_Inicio"}
_CAMPOS_DECIMAL = {
    "Valor",
    "QTD de Pessoas",
    "QTD de Diárias",
    "Valor diária - Outro Cargo",
    "Valor em U$ diária internacional",
    "Cotação Dolar/Real",
    "ValorConvertido",
    "Valor Inscrição",
    "InscricaoConvertida",
    "Valor Custo Complementar",
    "Valor Seguro Viagem",
    "Passagem individual",
    "Realizado",
}


def _converter(campo: str, texto: str):
    if texto == "":
        return None  # Blank()
    if campo in _CAMPOS_INT:
        return int(texto)
    if campo in _CAMPOS_DATA:
        return date.fromisoformat(texto)
    if campo in _CAMPOS_DECIMAL:
        return Decimal(texto)
    return texto


def ler_csv(caminho: Path | str) -> list[dict]:
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return [
            {campo: _converter(campo, valor) for campo, valor in linha.items()}
            for linha in csv.DictReader(f)
        ]


def carregar_eventos(pasta: Path = PASTA_DADOS) -> list[dict]:
    return ler_csv(pasta / "eventos.csv")


def carregar_custos(pasta: Path = PASTA_DADOS) -> list[dict]:
    return ler_csv(pasta / "custos.csv")


def carregar_diarias(pasta: Path = PASTA_DADOS) -> list[dict]:
    return ler_csv(pasta / "diarias.csv")


# ---------------------------------------------------------------------------
# Auxiliares com a semântica do Power Fx
# ---------------------------------------------------------------------------

DUAS_CASAS = Decimal("0.01")


def _n(valor: Optional[Decimal]) -> Decimal:
    """Blank em conta aritmética vale 0."""
    return Decimal(0) if valor is None else valor


def arredondar(valor: Decimal) -> Decimal:
    """Round(valor; 2) do Power Fx: metade para longe do zero."""
    return valor.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def nao_excluido(registro: dict) -> bool:
    """Equivale a Excluido <> "*"."""
    return registro.get("Excluido") != "*"


def formatar_reais(valor: Decimal, prefixo: str = "R$ ") -> str:
    """Text(valor; "[$-pt-BR]#.##0,00") precedido de "R$ ".

    DUVIDA-8: o arredondamento usado pelo Text() na exibição não está na
    fórmula; aqui usa-se o mesmo de Round() (metade para longe do zero).
    """
    v = arredondar(valor)
    sinal = "-" if v < 0 else ""
    inteiro, centavos = f"{abs(v):.2f}".split(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f"{prefixo}{sinal}{'.'.join(grupos)},{centavos}"


def _eventos_aprovados_do_ano(eventos: Iterable[dict], ano: int) -> list[dict]:
    return [
        e
        for e in eventos
        if e["Status de participação"] == "Aprovado"
        and e["DT_Inicio"].year == ano
        and nao_excluido(e)
    ]


# ---------------------------------------------------------------------------
# Regra 1 - Registros excluídos (resumo de eventos por ano)
# ---------------------------------------------------------------------------

STATUS_POR_COLUNA = {
    "EM_ABERTO": "Em Aberto",
    "EM_ANALISE": "Em Análise",
    "NAO_APROVADO": "Não Aprovado",
    "APROVADO": "Aprovado",
    "CANCELADO": "Cancelado",
    "APROVADO_AJUSTE": "Aprovado para ajustes",
}


def resumo_eventos_por_ano(eventos: Iterable[dict]) -> list[dict]:
    """Regra 1: contagem de eventos não excluídos por ano e por status.

    Retorna uma lista de dicts com as chaves ANO (coluna "Value" no Power Fx),
    QTD_EVENTOS e uma chave por status de STATUS_POR_COLUNA. Anos sem nenhum
    evento não excluído são omitidos. Ordem: ano decrescente.
    """
    eventos = list(eventos)
    nao_excluidos = [e for e in eventos if nao_excluido(e)]
    # anosDistintos vem de TODOS os eventos (inclusive excluídos); o filtro
    # QTD_EVENTOS <> 0 depois remove os anos que só têm excluídos.
    anos = {e["DT_Inicio"].year for e in eventos}

    resultado = []
    for ano in anos:
        do_ano = [e for e in nao_excluidos if e["DT_Inicio"].year == ano]
        linha = {"ANO": ano, "QTD_EVENTOS": len(do_ano)}
        for coluna, status in STATUS_POR_COLUNA.items():
            # DUVIDA-1: comparação de texto exata (maiúsculas/acentos).
            linha[coluna] = sum(
                1 for e in do_ano if e["Status de participação"] == status
            )
        if linha["QTD_EVENTOS"] != 0:
            resultado.append(linha)
    return sorted(resultado, key=lambda l: l["ANO"], reverse=True)


# ---------------------------------------------------------------------------
# Regra 2 - Valor de cada linha de custo
# ---------------------------------------------------------------------------


def _valor_diaria_lista(diarias: Iterable[dict], id_diaria: int) -> Optional[Decimal]:
    """LookUp(TB_DIARIAS_NACIONAIS; ID = id; Valor) - SEM filtrar excluídas,
    exatamente como na fórmula da regra 2 (ver DUVIDA-3)."""
    for d in diarias:
        if d["ID"] == id_diaria:
            return d["Valor"]
    return None


def _campo_obrigatorio(custo: dict, campo: str) -> Decimal:
    valor = custo.get(campo)
    if valor is None:
        # DUVIDA-5: a fórmula exibiria "R$ " seguido de texto vazio.
        raise ValueError(
            f"Linha de custo {custo.get('ID')}: campo '{campo}' vazio; "
            "comportamento indefinido (ver DUVIDAS.md, DUVIDA-5)."
        )
    return valor


def valor_linha_custo(custo: dict, diarias: Iterable[dict]) -> Optional[Decimal]:
    """Regra 2: valor em reais de uma linha de custo.

    Testa os casos na MESMA ordem do Switch da fórmula e usa o primeiro que
    se aplica. Retorna None quando nenhum caso se aplica (Switch sem padrão
    devolve Blank). Não filtra linhas excluídas: isso fica a cargo de quem
    chama (a fórmula atua sobre ThisItem de uma galeria).
    """
    tipo = custo.get("Tipo de Custo")
    pessoas = _n(custo.get("QTD de Pessoas"))
    qtd_diarias = _n(custo.get("QTD de Diárias"))

    if tipo == "Seguro Viagem":
        return _n(custo.get("Valor Seguro Viagem")) * pessoas

    if tipo == "Diária" and custo.get("Valor em U$ diária internacional") is not None:
        return _campo_obrigatorio(custo, "ValorConvertido")

    if tipo == "Passagem":
        return pessoas * _n(custo.get("Passagem individual"))

    if tipo == "Diária" and custo.get("ID_Diaria") is None:
        return qtd_diarias * _n(custo.get("Valor diária - Outro Cargo")) * pessoas

    if tipo == "Diária" and custo.get("ID_Diaria") is not None:
        # DUVIDA-2: aqui NÃO multiplica por QTD de Pessoas (regra 3 multiplica).
        return qtd_diarias * _n(_valor_diaria_lista(diarias, custo["ID_Diaria"]))

    if tipo == "Inscrição":
        return _campo_obrigatorio(custo, "InscricaoConvertida")

    if custo.get("Valor Custo Complementar") is not None:
        return custo["Valor Custo Complementar"]

    return None


def texto_linha_custo(custo: dict, diarias: Iterable[dict]) -> Optional[str]:
    """Regra 2 no formato exibido: "R$ #.##0,00" (None se Blank)."""
    valor = valor_linha_custo(custo, diarias)
    return None if valor is None else formatar_reais(valor)


# ---------------------------------------------------------------------------
# Regra 3 - Total previsto de custos
# ---------------------------------------------------------------------------


def previsto_linha_custo(custo: dict, diarias_ativas: list[dict]) -> Decimal:
    """Soma das sete partes de uma linha (cada uma arredondada a 2 casas).

    Não olha o Tipo de Custo: soma todos os campos preenchidos da linha.
    `diarias_ativas` já deve estar sem as diárias excluídas.
    """
    pessoas = _n(custo.get("QTD de Pessoas"))
    qtd_diarias = _n(custo.get("QTD de Diárias"))
    cotacao = _n(custo.get("Cotação Dolar/Real"))

    valor_lista = None
    if custo.get("ID_Diaria") is not None:
        valor_lista = next(
            (d["Valor"] for d in diarias_ativas if d["ID"] == custo["ID_Diaria"]),
            None,
        )

    diaria_outro_cargo = arredondar(
        qtd_diarias * _n(custo.get("Valor diária - Outro Cargo")) * pessoas
    )
    diaria_nacional = arredondar(qtd_diarias * _n(valor_lista) * pessoas)
    diaria_internacional = arredondar(
        (cotacao * _n(custo.get("Valor em U$ diária internacional")))
        * (qtd_diarias * pessoas)
    )
    # DUVIDA-6: qualquer moeda diferente de "US$" é tratada como reais.
    if custo.get("Moeda  - Inscrição") == "US$":
        inscricao = arredondar(cotacao * _n(custo.get("Valor Inscrição")))
    else:
        inscricao = arredondar(_n(custo.get("Valor Inscrição")))
    complementar = arredondar(_n(custo.get("Valor Custo Complementar")))
    seguro = arredondar(_n(custo.get("Valor Seguro Viagem")) * pessoas)
    passagem = arredondar(_n(custo.get("Passagem individual")) * pessoas)

    return (
        diaria_outro_cargo
        + diaria_nacional
        + diaria_internacional
        + inscricao
        + complementar
        + seguro
        + passagem
    )


def total_previsto(
    ano: int,
    eventos: Iterable[dict],
    custos: Iterable[dict],
    diarias: Iterable[dict],
) -> Decimal:
    """Regra 3: total previsto dos eventos aprovados e não excluídos do ano."""
    custos = list(custos)
    diarias_ativas = [d for d in diarias if nao_excluido(d)]
    total = Decimal(0)
    for evento in _eventos_aprovados_do_ano(eventos, ano):
        for custo in custos:
            if custo["ID_EVENTO"] == evento["ID"] and nao_excluido(custo):
                total += previsto_linha_custo(custo, diarias_ativas)
    # DUVIDA-7: sem eventos/linhas, o Sum() do Power Fx pode devolver 0 ou Blank.
    return total


def texto_total_previsto(ano, eventos, custos, diarias) -> str:
    return formatar_reais(total_previsto(ano, eventos, custos, diarias))


# ---------------------------------------------------------------------------
# Regra 4 - Total realizado
# ---------------------------------------------------------------------------


def total_realizado(ano: int, eventos: Iterable[dict], custos: Iterable[dict]) -> Decimal:
    """Regra 4: soma de Realizado das linhas não excluídas dos eventos
    aprovados e não excluídos do ano. Realizado vazio é ignorado (Sum)."""
    ids = {e["ID"] for e in _eventos_aprovados_do_ano(eventos, ano)}
    return sum(
        (
            c["Realizado"]
            for c in custos
            if nao_excluido(c) and c["ID_EVENTO"] in ids and c["Realizado"] is not None
        ),
        Decimal(0),
    )


def texto_total_realizado(ano, eventos, custos) -> str:
    """Formato exibido. DUVIDA-7: o "-" do Coalesce nunca é alcançado na
    fórmula original, pois "R$ " & ... nunca é Blank; aqui também não."""
    return formatar_reais(total_realizado(ano, eventos, custos))
