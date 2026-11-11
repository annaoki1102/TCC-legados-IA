# Estudo de caso – SIS Eventos

Material do estudo de caso descrito em `capitulos/proposta.tex` e `capitulos/descricao_sistema.tex`. Todos os dados são **inventados** (nada real).

- `formulas/` – as fórmulas originais do Power Apps, uma por arquivo, com a descrição da regra e a tela/controle/propriedade de origem no topo:
  - `01_registros_excluidos.txt` – registros marcados com `*` (simples)
  - `02_valor_linha_custo.txt` – valor de cada linha de custo (média)
  - `03_total_previsto.txt` – total previsto de custos dos eventos aprovados de um ano (complexa)
  - `04_total_realizado.txt` – total realizado dos eventos aprovados de um ano (regra extra)
- `dados/` – dados inventados para os testes, com os mesmos nomes de campos das fórmulas. CSV em UTF-8, separador `,`, decimais com ponto, campo vazio = sem valor, `*` em `Excluido` = registro excluído.
  - `eventos.csv` – como `TB_EVENTOS` (10 eventos, anos 2025 e 2026, todos os status)
  - `custos.csv` – como `TB_PREVISAO_CUSTO_EVENTOS` (23 linhas de custo)
  - `diarias.csv` – como `TB_DIARIAS_NACIONAIS` (3 diárias, uma excluída)
- `harness/` – roteiro para rodar as fórmulas no Power Apps sem tocar no app real:
  - `teste_app_vazio.txt` – passo a passo para criar um app vazio, com o `App.OnStart` que carrega os dados de `dados/` e as fórmulas para colar nos controles.
- `resultados_esperados.csv` – resultados obtidos no sistema atual (colunas `regra`, `caso`, `resultado_sistema_atual`). Começa vazio e é preenchido rodando o roteiro de `harness/`. Serve de referência para conferir o código novo.
