import sys, csv
from decimal import Decimal
from collections import defaultdict
BASE = "C:/Users/anna.correa/TCC-legados-IA/estudo-caso"
sys.path.insert(0, BASE + "/conversao_v2"); import regras as R
print("regras importado de:", R.__file__)
ev, cu, di = R.carregar_eventos(), R.carregar_custos(), R.carregar_diarias()
print("pasta de dados:", R.PASTA_DADOS, "| eventos", len(ev), "custos", len(cu), "diarias", len(di))
col = {"Total":"QTD_EVENTOS","Em Aberto":"EM_ABERTO","Em Análise":"EM_ANALISE","Não Aprovado":"NAO_APROVADO","Aprovado":"APROVADO","Cancelado":"CANCELADO","Aprovado para ajustes":"APROVADO_AJUSTE"}
r1 = R.resumo_eventos_por_ano(ev)
print("ordem dos anos regra 1:", [l["ANO"] for l in r1])
cont = defaultdict(lambda: [0, 0]); falhas = []; difs_texto = []
for l in csv.DictReader(open(BASE + "/resultados_esperados.csv", encoding="utf-8")):
    r, c, esp, txt = l["regra"], l["caso"], l["resultado_sistema_atual"], l["texto_na_tela"]
    t = None
    try:
        if r == "01":
            ano = int(c.split()[1]); st = c.split(" - ", 1)[1]
            v = [x for x in r1 if x["ANO"] == ano][0][col[st]]; t = str(v)
            ok_v = (v == int(esp))
        else:
            ano_ou_id = int(c.split()[1])
            if r == "02":
                cc = [x for x in cu if x["ID"] == ano_ou_id][0]
                v = R.valor_linha_custo(cc, di); t = R.texto_linha_custo(cc, di)
            elif r == "03":
                v = R.total_previsto(ano_ou_id, ev, cu, di); t = R.texto_total_previsto(ano_ou_id, ev, cu, di)
            else:
                v = R.total_realizado(ano_ou_id, ev, cu); t = R.texto_total_realizado(ano_ou_id, ev, cu)
            ok_v = (v is not None and Decimal(esp) == v)
    except Exception as e:
        v = f"ERRO {type(e).__name__}: {e}"; ok_v = False
    ok_t = (t == txt)
    cont[r][0 if ok_v else 1] += 1
    if not ok_v: falhas.append((r, c, esp, v))
    if not ok_t: difs_texto.append((r, c, txt, t))
print("\nPOR REGRA (valor): regra -> batem / não batem")
for r in sorted(cont): print(" ", r, "->", cont[r][0], "/", cont[r][1])
print("total:", sum(x[0] for x in cont.values()), "/", sum(x[1] for x in cont.values()))
print("\nVALORES QUE NÃO BATEM:"); [print(" ", f) for f in falhas] or print("  nenhum")
print("\nTEXTOS DIFERENTES:"); [print(" ", d) for d in difs_texto] or print("  nenhum")
