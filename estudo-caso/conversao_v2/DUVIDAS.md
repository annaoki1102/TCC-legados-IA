# Dúvidas da conversão Power Fx → Python

Nos pontos abaixo, o código em `regras.py` segue **literalmente a fórmula**
(não a descrição) e marca o trecho com `DUVIDA-n`. Cada item precisa de
confirmação de quem conhece o negócio.

## DUVIDA-1: comparação de texto (status e `Excluido`)
- Regras 1, 3 e 4 comparam `'Status de participação'.Value = "Aprovado"` e
  `Excluido <> "*"`.
- O código compara o texto exato. Não se sabe se a fonte original
  (SharePoint/Dataverse) compara sem diferenciar maiúsculas/acentos, nem se
  `Excluido` pode ter variações (`" *"`, `"**"`, `"x"`).
- Também não se sabe o que fazer com um evento sem `DT_Inicio`
  (`Year(Blank())`). Hoje o código dá erro nesse caso. Os dados não têm esse caso.

## DUVIDA-2: diária nacional multiplica ou não pela quantidade de pessoas?
- **Regra 2** (fórmula e descrição): `QTD de Diárias × Valor da lista`, **sem** pessoas.
- **Regra 3**: `QTD de Diárias × Valor da lista × QTD de Pessoas`.
- Efeito nos dados: a linha de custo 4 (2 pessoas, 2 diárias de R$ 400) mostra
  **R$ 800,00** na regra 2 e entra com **R$ 1.600,00** no total previsto.
  O `Realizado` dessa linha é 1600, o que sugere que a regra 2 está errada,
  mas isso não foi confirmado.

## DUVIDA-3: diária nacional excluída
- A descrição da regra 1 diz que diárias marcadas com `*` são ignoradas "nas contas".
- **Regra 2** faz `LookUp(TB_DIARIAS_NACIONAIS; ...)` **sem** filtrar as excluídas.
- **Regra 3** filtra as excluídas (`Filter(TB_DIARIAS_NACIONAIS; Excluido <> "*")`),
  então o valor vira Blank → 0.
- Efeito nos dados: a linha de custo 5 usa a diária 3 (excluída, R$ 500). A regra 2
  mostra **R$ 1.000,00**, mas a linha contribui **R$ 0,00** no total previsto.
  O `Realizado` dela é 1000.
- Não se sabe se o certo é ignorar o valor, usar o valor antigo ou bloquear a linha.

## DUVIDA-4: valor guardado × valor calculado (diária internacional e inscrição)
- **Regra 2** mostra os campos já guardados na linha (`ValorConvertido`,
  `InscricaoConvertida`).
- **Regra 3** recalcula: `Cotação × Valor US$ × diárias × pessoas` e
  `Cotação × Valor Inscrição` (quando a moeda é US$).
- Nos CSV atuais os dois batem (linhas 10, 11 e 12). Se divergirem (ex.: a
  cotação mudou depois da gravação), não se sabe qual é a fonte da verdade.

## DUVIDA-5: campo convertido vazio na regra 2
- Se `Tipo = "Diária"` com valor em US$ preenchido mas `ValorConvertido` vazio
  (ou `Tipo = "Inscrição"` com `InscricaoConvertida` vazio), o Power Apps
  exibiria `"R$ "` seguido de texto vazio.
- Não se sabe se deveria mostrar R$ 0,00, recalcular ou indicar erro.
  O código levanta `ValueError`. Os dados não têm esse caso.

## DUVIDA-6: moeda da inscrição diferente de "US$"
- A regra 3 só converte quando `'Moeda  - Inscrição' = "US$"`. Qualquer outro
  valor (inclusive vazio, "EUR" etc.) é tratado como reais.
- Não se sabe se existem outras moedas. Os dados só têm `R$` e `US$`.

## DUVIDA-7: totais sem nenhum registro (regras 3 e 4)
- Na regra 4, `Coalesce("R$ " & Text(...); "-")` nunca chega ao `"-"`, porque
  `"R$ " & ...` nunca é Blank. Parece que a intenção era mostrar `"-"` quando
  não houvesse lançamentos, mas a fórmula não faz isso.
- Também não se sabe se `Sum` de tabela vazia daria 0 ou Blank no app.
- O código devolve `Decimal(0)` / `"R$ 0,00"`.

## DUVIDA-8: arredondamento na exibição
- `Text(valor; "#.##0,00")` não diz como arredondar valores com mais de duas
  casas. O código usa o mesmo critério do `Round` (metade para longe do zero).
  Os dados atuais só têm valores inteiros, então isso não altera os testes.

## Observações (não são dúvidas, mas vale registrar)
- **Ordem dos casos da regra 2:** a descrição lista Seguro, Passagem, Diária
  internacional, Diária nacional, Diária de outro cargo...; a fórmula testa
  Seguro, Diária internacional, Passagem, Diária de outro cargo, Diária nacional...
  Como os casos não se sobrepõem, o resultado é o mesmo. O código segue a ordem
  da fórmula, em que a diária internacional vem antes das outras diárias.
- **A regra 2 não filtra linhas excluídas.** Ela calcula uma linha (`ThisItem`).
  O filtro fica a cargo da galeria, que está fora das fórmulas.
- **A regra 3 soma todos os campos sem olhar o tipo.** Isso está escrito na
  descrição, então foi mantido. Uma linha com campos de outro tipo preenchidos
  por engano será somada em dobro.
