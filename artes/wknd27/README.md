# RGNR Weekend ’27 — Salve essa data

Arte genérica para divulgar a data do WKND ’27. Tema: **Awaken (desperta)**, com amanhecer, verão e cores quentes.
São 4 opções, cada uma em **Feed (1080×1350)** e **Story (1080×1920)**. Os arquivos finais estão em [`export/`](export/).

| # | Opção | Linguagem |
|---|-------|-----------|
| 01 | **Horizonte** | Cinematográfica: o sol nasce atrás das letras de AWAKEN, que se refletem no mar. Céu da noite para o dourado. |
| 02 | **Sol** | Editorial/gráfica: o sol é o “0” do 06, nascendo no horizonte, com laranja chapado e tipografia pesada. |
| 03 | **Verão** | Retrô anos 70: selo de sol com texto em arco, raios ao fundo e ondas. |
| 04 | **Luz** | Clara e etérea: luz da manhã estourada, serifa itálica e colinas. Traz a referência “Desperta, tu que dormes…” (Ef 5.14), que pode ser removida. |

Texto usado em todas: **SALVE ESSA DATA!**, **SÁBADO – 06 FEV** e **RGNR Weekend ’27**, mais o tema AWAKEN / desperta.

## Logos

Os logos **RGNR** e **IPDA** nas artes são **provisórios** (só o nome em texto). Para trocar pelos oficiais:

1. Salve `rgnr.svg` e `ipda.svg` (ou `.png` com fundo transparente) na pasta [`logos/`](logos/).
2. Rode `node render.js`.

Cada logo é recolorido automaticamente na cor da arte. Para manter as cores originais, crie um arquivo vazio `logos/manter-cores`.

## Gerar de novo

Requer Node e Playwright (`npm i playwright`).

```bash
node render.js            # todas as artes + export/wknd27-visao-geral.jpg
node render.js 03 story   # só uma opção e/ou um formato
```

As artes são HTML/SVG em [`src/`](src/), um arquivo por opção. As cores e posições ficam no topo de cada arquivo.
