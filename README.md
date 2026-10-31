# Desafios da modernização de sistemas legados com agentes de IA no desenvolvimento de software

**Autora:** Anna Beatriz Resende Oki Corrêa

## Resumo

Sistemas legados guardam regras de negócio importantes, mas usam tecnologias antigas e são caros de manter. Agentes de IA para o desenvolvimento, como o Claude Code, podem ajudar a modernizá-los, mas os estudos mostram limites: o desempenho cai em projetos grandes e parte das regras do sistema pode deixar de ser migrada. Este trabalho busca responder quais são os desafios para converter e atualizar sistemas legados para novas tecnologias por meio de agentes de IA, do ponto de vista do desenvolvimento.

## Situação atual

O texto do TCC está em andamento.

## Onde está cada coisa

| Arquivo ou pasta | O que tem |
|------------------|-----------|
| `TCC.tex` | Versão atual do TCC: arquivo principal, que junta todos os capítulos. |
| `capitulos/cap1_introducao.tex` | Introdução: problema, objetivos e metodologia. |
| `capitulos/cap2_*.tex` | Fundamentação teórica: sistemas legados, agentes de IA, verificação e desafios. |
| `capitulos/proposta.tex` | Proposta e plano de avaliação. |
| `capitulos/consideracoes_finais.tex` | Considerações finais. |
| `TCC.bib` | Referências bibliográficas (BibTeX). |
| `images/` | Figuras usadas no texto. |
| `sty/` | Pacotes e estilos (`.sty`) auxiliares. |

## Como compilar

O texto é escrito em LaTeX, com a classe [abntex2](https://www.abntex.net.br/).

**Pré-requisitos:** uma distribuição LaTeX (MiKTeX ou TeX Live), Perl e `latexmk`.

Pelo terminal, na raiz do projeto:

```
latexmk -pdf TCC.tex
```

Ou, no VS Code, com a extensão **LaTeX Workshop**: abra `TCC.tex` e compile pelo botão *Build LaTeX project* (ou salve o arquivo, se a compilação automática estiver ativa).

O PDF gerado é `TCC.pdf`, que fica versionado. Os demais arquivos de compilação (`.aux`, `.log`, `.bbl` etc.) são ignorados pelo git.

## Trabalhando em mais de uma máquina

1. Ao começar: `git pull`
2. Ao terminar:
   ```
   git add .
   git commit -m "descrição do que mudou"
   git push
   ```

## Aviso

Este repositório é **privado** e deve continuar assim até a defesa do TCC.
