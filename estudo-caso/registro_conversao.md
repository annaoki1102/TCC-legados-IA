# Registro da conversão para Python

- Data: 2026-11-11
- Agente: Claude Code (modelo Claude Opus 5.5)
- Código: `python/regras.py`. Testes: `python/testes/test_regras.py`.
- Dados: `dados/*.csv`. Valores esperados: `resultados_esperados.csv` (coluna `resultado_sistema_atual`, e `texto_na_tela` para o texto).
- Comando: `python -m pytest -p no:cacheprovider testes` (na pasta `python/`), com Python 3.11.4 e pytest 9.2.0. O pytest foi instalado nesta etapa (`pip install --user pytest`).
- Resultado final: 42 testes, 42 passaram, 0 falharam.

Os testes leem os valores esperados do CSV. O único texto fixo no arquivo de testes é o mapa entre os rótulos da coluna `caso` da regra 01 (ex.: "Em Aberto") e os nomes das colunas que a fórmula 01 cria (ex.: `EM_ABERTO`).

## Fatos que valem para todas as regras

- O mesmo agente que converteu as regras também criou, nas etapas anteriores, os dados inventados (`dados/*.csv`), o roteiro do app de teste (`harness/teste_app_vazio.txt`) e as contas à mão dos totais de 2026 (03 = 19.450,00; 04 = 20.350,00) e de 2025. Os resultados do sistema atual foram observados pela autora no app de teste.
- A coluna `texto_na_tela` das regras 02, 03 e 04 foi montada pelo agente a partir do formato das fórmulas (`#.##0,00`), com os valores informados pela autora. Esse texto não foi copiado da tela.
- Todos os valores dos dados são inteiros. Nenhum caso testa arredondamento de centavos.
- Campos vazios do CSV viraram `None`, que vale 0 nas contas, como `Blank()` no Power Fx.

## Regra 01 – registros excluídos / eventos por ano

- **O que o agente entendeu:** a regra pega os anos de todos os eventos, inclusive dos excluídos. Para cada ano, conta só os eventos não excluídos (`Excluido <> "*"`), no total e por status. Depois tira os anos com total 0 e ordena do maior ano para o menor.
- **O que errou na primeira versão:** nada. Os testes passaram na primeira execução.
- **O que ficou ambíguo na fórmula original:**
  - Um ano que só tem eventos excluídos aparece na lista de anos, mas sai pelo filtro `QTD_EVENTOS <> 0`. Os dados não têm um ano assim, então esse caso não foi testado.
  - `Year(DT_Inicio)` pode depender do fuso horário quando a data vem com hora no SharePoint. Nos dados só há datas, sem hora.
  - A coluna da galeria se chama `Value`, por causa do `Distinct`.
- **Tentativas:** 1.
- **Passou:** sim. Foram 14 testes de contagem mais 1 teste da ordem dos anos.

## Regra 02 – valor de cada linha de custo

- **O que o agente entendeu:** é um `Switch(true; ...)`. A regra testa sete casos em ordem: seguro, diária internacional, passagem, diária de outro cargo, diária da lista, inscrição e custo complementar. Usa o primeiro que se aplica. Se nenhum caso se aplica, o resultado é vazio.
- **O que errou na primeira versão:** nada. Os testes passaram na primeira execução.
- **Comportamentos do sistema antigo que foram mantidos:**
  - A fórmula não olha o campo `Excluido` da linha. O custo 9 está excluído e mesmo assim dá 800,00.
  - A diária da lista não é multiplicada pela quantidade de pessoas. O custo 4 dá 800,00 (2 diárias × 400), com 2 pessoas.
  - A diária da lista usa `TB_DIARIAS_NACIONAIS` sem filtrar as diárias excluídas. O custo 5 usa a diária 3, que está excluída, e dá 1000,00.
  - A diária internacional e a inscrição mostram os campos guardados `ValorConvertido` e `InscricaoConvertida`, e não fazem conta.
  - O custo complementar não testa o tipo de custo, só se o valor está preenchido.
- **O que ficou ambíguo na fórmula original:**
  - De onde vêm `ValorConvertido` e `InscricaoConvertida` (é o TODO de `descricao_sistema.tex`).
  - O que aparece quando nenhum caso se aplica, ou quando o campo convertido está vazio. O código devolve `None` e o texto "R$ ", porque `Text(Blank())` dá texto vazio. Esse caso não foi testado.
  - O arredondamento acontece só na hora de formatar o texto.
- **Tentativas:** 1.
- **Passou:** sim, nos 23 testes. Cada teste confere o valor e o texto.

## Regra 03 – total previsto de custos

- **O que o agente entendeu:** a regra pega os eventos com status "Aprovado", do ano de `VarAnoExercicioSelecionado` e não excluídos. Para cada um, pega as linhas de custo não excluídas. Cada linha soma sete partes, cada parte com `Round(...; 2)`, sem olhar o tipo de custo. A diária nacional busca o valor só entre as diárias não excluídas. A inscrição multiplica pela cotação quando `'Moeda  - Inscrição' = "US$"`.
- **O que errou na primeira versão:** nada. Os testes passaram na primeira execução.
- **O que ficou ambíguo na fórmula original:**
  - Em `Filter(TB_PREVISAO_CUSTO_EVENTOS As PC; PC.ID_EVENTO = ID ...)`, o agente entendeu que `ID` é o ID do evento, que vem do `ForAll`, e não o ID da linha de custo.
  - Em `LookUp(...; ID = ID_Diaria; Valor)`, o agente entendeu que `ID` e `Valor` são da diária, e `ID_Diaria` é da linha de custo.
  - O agente supôs que `Round` arredonda para longe do zero e usou `ROUND_HALF_UP`. Isso não foi testado, porque os dados só têm valores inteiros.
  - A conta soma todos os campos da linha. Uma linha com campos de mais de um tipo somaria todos eles, mas os dados não têm uma linha assim.
  - A comparação com "US$" é exata. Outra grafia, como "USD", cai no caso do real.
  - A conta da regra 03 é diferente da regra 02 nos custos 4 e 5. Ela multiplica a diária nacional pelas pessoas e ignora a diária excluída. Por isso, em 2026, a parte do evento 1 no total é 6.350, e a soma das linhas da regra 02 desse evento, sem o custo 9, é 6.550.
- **Tentativas:** 1.
- **Passou:** sim, nos 2 testes (2026 e 2025). Cada teste confere o valor e o texto.

## Regra 04 – total realizado

- **O que o agente entendeu:** soma o campo `Realizado` das linhas não excluídas dos eventos aprovados, não excluídos, do ano. Campos `Realizado` vazios ficam de fora da soma.
- **O que errou na primeira versão:** nada. Os testes passaram na primeira execução.
- **O que ficou ambíguo na fórmula original:**
  - Em `Coalesce("R$ " & Text(...); "-")`, o primeiro argumento sempre começa com "R$ ", então nunca é vazio, e o "-" não aparece. O código não devolve "-".
  - O total não é arredondado antes de formatar.
  - Em 2025, o total realizado (1.000,00) é igual ao previsto, porque nos dados o realizado do evento 10 é igual ao previsto.
- **Tentativas:** 1.
- **Passou:** sim, nos 2 testes (2026 e 2025).

## Casos que não foram testados

- Valores com centavos e arredondamento.
- Linha de custo sem nenhum caso aplicável na regra 02, ou com `ValorConvertido` / `InscricaoConvertida` vazio.
- Ano que só tem eventos excluídos (regra 01).
- Ano sem eventos aprovados (regras 03 e 04).
- Linha de custo com campos de mais de um tipo preenchidos (regra 03).
