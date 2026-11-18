from datetime import date
from decimal import Decimal

import pytest

import regras as r

D = Decimal


@pytest.fixture(scope="module")
def eventos():
    return r.carregar_eventos()


@pytest.fixture(scope="module")
def custos():
    return r.carregar_custos()


@pytest.fixture(scope="module")
def diarias():
    return r.carregar_diarias()


def custo_por_id(custos, id_):
    return next(c for c in custos if c["ID"] == id_)


# ---------------------------------------------------------------- leitura


def test_leitura_converte_tipos(custos, eventos):
    c = custo_por_id(custos, 1)
    assert c["Valor Seguro Viagem"] == D("100")
    assert isinstance(c["Valor Seguro Viagem"], Decimal)
    assert c["ID_Diaria"] is None  # vazio vira Blank/None
    assert eventos[0]["DT_Inicio"] == date(2026, 3, 10)


def test_formatar_reais():
    assert r.formatar_reais(D("19450")) == "R$ 19.450,00"
    assert r.formatar_reais(D("0")) == "R$ 0,00"
    assert r.formatar_reais(D("1234567.891")) == "R$ 1.234.567,89"
    assert r.formatar_reais(D("999.995")) == "R$ 1.000,00"
    assert r.formatar_reais(D("-1500.5")) == "R$ -1.500,50"


def test_arredondar_metade_longe_do_zero():
    assert r.arredondar(D("0.125")) == D("0.13")
    assert r.arredondar(D("-0.125")) == D("-0.13")
    assert r.arredondar(D("0.124")) == D("0.12")


# ---------------------------------------------------------------- regra 1


def test_regra1_resumo_por_ano(eventos):
    resumo = r.resumo_eventos_por_ano(eventos)
    assert [l["ANO"] for l in resumo] == [2026, 2025]  # decrescente
    assert resumo[0] == {
        "ANO": 2026,
        "QTD_EVENTOS": 7,  # o evento 9 (excluído) não conta
        "EM_ABERTO": 1,
        "EM_ANALISE": 1,
        "NAO_APROVADO": 1,
        "APROVADO": 3,
        "CANCELADO": 0,
        "APROVADO_AJUSTE": 1,
    }
    assert resumo[1] == {
        "ANO": 2025,
        "QTD_EVENTOS": 2,
        "EM_ABERTO": 0,
        "EM_ANALISE": 0,
        "NAO_APROVADO": 0,
        "APROVADO": 1,
        "CANCELADO": 1,
        "APROVADO_AJUSTE": 0,
    }


def test_regra1_ano_so_com_excluidos_some():
    eventos = [
        {"ID": 1, "DT_Inicio": date(2024, 1, 1), "Status de participação": "Aprovado", "Excluido": "*"},
        {"ID": 2, "DT_Inicio": date(2023, 1, 1), "Status de participação": "Aprovado", "Excluido": None},
    ]
    assert [l["ANO"] for l in r.resumo_eventos_por_ano(eventos)] == [2023]


def test_regra1_aprovado_para_ajustes_nao_conta_como_aprovado():
    eventos = [
        {"ID": 1, "DT_Inicio": date(2026, 1, 1), "Status de participação": "Aprovado para ajustes", "Excluido": None},
    ]
    linha = r.resumo_eventos_por_ano(eventos)[0]
    assert linha["APROVADO"] == 0 and linha["APROVADO_AJUSTE"] == 1


# ---------------------------------------------------------------- regra 2

ESPERADO_REGRA2 = {
    1: "200",    # seguro 100 x 2
    2: "2000",   # passagem 2 x 1000
    3: "900",    # diária lista 3 x 300
    4: "800",    # diária lista 2 x 400 (sem pessoas, ver DUVIDA-2)
    5: "1000",   # diária 3 (excluída) ainda é usada, ver DUVIDA-3
    6: "1000",   # outro cargo 2 x 250 x 2
    7: "500",    # InscricaoConvertida
    8: "150",    # custo complementar
    9: "800",    # linha excluída: a regra 2 não filtra
    10: "500",   # ValorConvertido
    11: "6000",
    12: "1500",
    13: "5000",
    14: "100",
    15: "700",
    16: "80",
    17: "400",
    18: "900",
    19: "250",
    20: "1200",
    21: "60",
    22: "600",
    23: "400",
}


@pytest.mark.parametrize("id_custo,esperado", ESPERADO_REGRA2.items())
def test_regra2_valor_por_linha(custos, diarias, id_custo, esperado):
    assert r.valor_linha_custo(custo_por_id(custos, id_custo), diarias) == D(esperado)


def test_regra2_texto(custos, diarias):
    assert r.texto_linha_custo(custo_por_id(custos, 11), diarias) == "R$ 6.000,00"


def test_regra2_internacional_tem_prioridade_sobre_outro_cargo(diarias):
    custo = {
        "Tipo de Custo": "Diária",
        "QTD de Pessoas": D(1),
        "QTD de Diárias": D(1),
        "ID_Diaria": None,
        "Valor diária - Outro Cargo": D(999),
        "Valor em U$ diária internacional": D(10),
        "ValorConvertido": D(50),
    }
    assert r.valor_linha_custo(custo, diarias) == D(50)


def test_regra2_nenhum_caso_retorna_none(diarias):
    custo = {"Tipo de Custo": None, "QTD de Pessoas": D(1), "Valor Custo Complementar": None}
    assert r.valor_linha_custo(custo, diarias) is None
    assert r.texto_linha_custo(custo, diarias) is None


def test_regra2_campo_convertido_vazio_levanta_erro(diarias):
    custo = {"ID": 99, "Tipo de Custo": "Inscrição", "InscricaoConvertida": None}
    with pytest.raises(ValueError, match="DUVIDA-5"):
        r.valor_linha_custo(custo, diarias)


def test_regra2_campos_vazios_valem_zero(diarias):
    custo = {"Tipo de Custo": "Passagem", "QTD de Pessoas": D(3), "Passagem individual": None}
    assert r.valor_linha_custo(custo, diarias) == D(0)


# ---------------------------------------------------------------- regra 3


def test_regra3_total_2026(eventos, custos, diarias):
    # Evento 1: 200+2000+900+1600+0+1000+500+150 = 6350
    #   (linha 5 usa diária excluída -> 0; linha 9 excluída)
    # Evento 2: 500+6000+1500+5000+100 = 13100
    # Evento 3: sem custos; evento 9: excluído
    assert r.total_previsto(2026, eventos, custos, diarias) == D("19450.00")
    assert r.texto_total_previsto(2026, eventos, custos, diarias) == "R$ 19.450,00"


def test_regra3_total_2025(eventos, custos, diarias):
    # Evento 10: 600 + 2x200x1 = 1000 (evento 7 é Cancelado)
    assert r.total_previsto(2025, eventos, custos, diarias) == D("1000.00")


def test_regra3_ano_sem_eventos(eventos, custos, diarias):
    assert r.total_previsto(2020, eventos, custos, diarias) == D(0)


def test_regra3_diaria_nacional_multiplica_pessoas(custos, diarias):
    ativas = [d for d in diarias if r.nao_excluido(d)]
    assert r.previsto_linha_custo(custo_por_id(custos, 4), ativas) == D("1600.00")


def test_regra3_soma_todos_os_campos_sem_olhar_tipo():
    custo = {
        "Tipo de Custo": "Passagem",
        "QTD de Pessoas": D(2),
        "Passagem individual": D(100),
        "Valor Seguro Viagem": D(10),  # preenchido "por engano"
    }
    assert r.previsto_linha_custo(custo, []) == D("220.00")


def test_regra3_arredonda_cada_parte():
    custo = {
        "QTD de Pessoas": D(1),
        "Passagem individual": D("0.005"),
        "Valor Seguro Viagem": D("0.005"),
    }
    # cada parte vira 0.01 -> 0.02 (arredondar a soma daria 0.01)
    assert r.previsto_linha_custo(custo, []) == D("0.02")


def test_regra3_inscricao_em_dolar_e_em_real():
    dolar = {"Moeda  - Inscrição": "US$", "Cotação Dolar/Real": D("5.1"), "Valor Inscrição": D(100)}
    real = {"Moeda  - Inscrição": "R$", "Cotação Dolar/Real": D("5.1"), "Valor Inscrição": D(100)}
    assert r.previsto_linha_custo(dolar, []) == D("510.00")
    assert r.previsto_linha_custo(real, []) == D("100.00")


# ---------------------------------------------------------------- regra 4


def test_regra4_total_2026(eventos, custos):
    # Evento 1 (sem a linha 9): 200+1900+900+1600+1000+1000+500+150 = 7250
    # Evento 2: 500+6000+1500+5000+100 = 13100
    assert r.total_realizado(2026, eventos, custos) == D("20350")
    assert r.texto_total_realizado(2026, eventos, custos) == "R$ 20.350,00"


def test_regra4_total_2025(eventos, custos):
    assert r.total_realizado(2025, eventos, custos) == D("1000")


def test_regra4_ignora_evento_excluido_e_nao_aprovado(eventos, custos):
    # Evento 9 (excluído, 1260 realizados) e eventos não aprovados ficam fora.
    ids_considerados = {1, 2, 3}
    esperado = sum(
        (c["Realizado"] for c in custos
         if c["ID_EVENTO"] in ids_considerados and r.nao_excluido(c) and c["Realizado"] is not None),
        D(0),
    )
    assert r.total_realizado(2026, eventos, custos) == esperado


def test_regra4_ano_sem_eventos(eventos, custos):
    assert r.texto_total_realizado(2020, eventos, custos) == "R$ 0,00"
