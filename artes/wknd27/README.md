# RGNR Weekend ’27 — Salve essa data

Arte genérica para divulgar a data do WKND ’27. Tema: **Awaken (desperta)**, com amanhecer, verão e cores quentes.
São 10 opções, cada uma em **Feed (1080×1350)** e **Story (1080×1920)**. Os arquivos finais estão em [`export/`](export/), com uma folha de visão geral para cada grupo (`wknd27-visao-geral.jpg` e `wknd27-visao-geral-referencias.jpg`).

| # | Opção | Linguagem |
|---|-------|-----------|
| 01 | **Horizonte** | Cinematográfica: o sol nasce atrás das letras de AWAKEN, que se refletem no mar. Céu da noite para o dourado. |
| 02 | **Sol** | Editorial/gráfica: o sol é o “0” do 06, nascendo no horizonte, com laranja chapado e tipografia pesada. |
| 03 | **Verão** | Retrô anos 70: selo de sol com texto em arco, raios ao fundo e ondas. |
| 04 | **Luz** | Clara e etérea: luz da manhã estourada, serifa itálica e colinas. Traz a referência “Desperta, tu que dormes…” (Ef 5.14), que pode ser removida. |

### A partir das referências (05 a 10)

Cada uma segue uma das referências que foram enviadas, adaptada ao tema e às cores quentes de verão.

| # | Opção | Referência | Linguagem |
|---|-------|------------|-----------|
| 05 | **Granulado** | “Love your enemies” | Degradê granulado, SALVE / DATA! gigante com letras encostadas e “Essa” em script por cima. |
| 06 | **Escada** | “We only fall to rise again” | Blocos em escada 3D subindo: SALVE ESSA → DATA! → SÁBADO → 06 FEV → RGNR → WEEKEND ’27. |
| 07 | **Desfoque** | “Inter Session” | Fundo cinza claro, RGNR ’27 / WEEKEND em degradê com letras misturadas e desfoque nas pontas. |
| 08 | **Jornal** | Estilo periódico | Página de jornal rasgada sobre laranja, xilogravura de nascer do sol, fita com a data e carimbo. |
| 09 | **Gigante** | “Overthink” | 06 / FEV gigante ocupando a arte toda, com o texto pequeno dentro do vão do E. |
| 10 | **Telão** | “All Church Prayer” | Letreiro de telão de LED: linhas cortadas nas bordas, condensada + script “Awaken”. |

Versículos usados (ARC): Ef 5.14 na 04; Is 60.1 na 07; Is 60.1, Rm 13.11-12 e Ef 5.14 na 08. Dá para trocar ou tirar.

Texto usado em todas: **SALVE ESSA DATA!**, **SÁBADO – 06 FEV** e **RGNR Weekend ’27**, mais o tema AWAKEN / desperta.

## Logos

Os logos **RGNR** e **IPDA** nas artes são **provisórios** (só o nome em texto). Para trocar pelos oficiais:

1. Salve `rgnr.svg` e `ipda.svg` (ou `.png` com fundo transparente) na pasta [`logos/`](logos/).
2. Rode `node render.js`.

Cada logo é recolorido automaticamente na cor da arte. Para manter as cores originais, crie um arquivo vazio `logos/manter-cores`.

## Gerar de novo

Requer Node e Playwright (`npm i playwright`).

```bash
node render.js            # todas as artes + as folhas de visão geral
node render.js 03 story   # só uma opção e/ou um formato
```

As artes são HTML/SVG em [`src/`](src/), um arquivo por opção. As cores e posições ficam no topo de cada arquivo.
