# Culto RGNR — Fim do Mundo (PSD editável)

Reconstrução em camadas da arte de divulgação do culto **Fim do Mundo** (21 NOV, 19 horas), feita a partir da imagem final em [`referencia/original.webp`](referencia/original.webp) (1080×1350). O arquivo original em camadas não foi encontrado.

- **PSD:** [`export/culto-rgnr-fim-do-mundo.psd`](export/culto-rgnr-fim-do-mundo.psd)
- **Prévia da reconstrução:** [`export/fim-do-mundo.png`](export/fim-do-mundo.png)

## Camadas

| Grupo / camada | O que é |
|---|---|
| **INFORMAÇÕES** | `21 NOV`, `19 HORAS`, `Endereço` (2 linhas) e `Transfer` (3 linhas, alinhado à direita). Todas são camadas de texto editáveis. |
| **TÍTULO** | `FIM DO MUNDO` e `CULTO RGNR` como texto editável, cada um com a **Textura** creme/ferrugem por cima, em máscara de recorte. Ao trocar o texto, a textura acompanha. |
| **Logo regenere** | Logo recortado da própria imagem, em baixa resolução. Troque pelo arquivo oficial. |
| **Fundo — Terra** | A imagem de fundo com todos os textos e o logo removidos. |

## Fontes

Instale antes de abrir:

- **Anton** (Google Fonts): data, hora, "CULTO RGNR" e o título. Usa **escala horizontal de 88%** para ficar com a largura da arte original.
- **Inter Tight Black** (Google Fonts): endereço e transfer.

O título original parece ser **Tusker Grotesk**, que não estava disponível aqui. Para usar a fonte da marca, selecione as camadas de texto e troque a fonte. Depois ajuste o tamanho e volte a escala horizontal para 100%.

Ao abrir o PSD, o Photoshop pergunta se quer atualizar as camadas de texto: clique em **Atualizar**.

## Limitações

- Atrás das letras, o fundo foi **reconstruído** (preenchido a partir da imagem ao redor), porque ali não existia imagem original. Com os textos no lugar não aparece nada. Se o título for movido ou apagado, pode aparecer alguma marca na parte da Terra em chamas.
- O logo vem da própria imagem (128×38 px). Para impressão ou ampliação, use o arquivo original.

## Gerar de novo

Requer Node, `npm i ag-psd pngjs playwright`.

```bash
node psd.js   # gera export/culto-rgnr-fim-do-mundo.psd e export/fim-do-mundo.png
```

A arte está em [`src/fim-do-mundo.html`](src/fim-do-mundo.html). Lá ficam o fundo limpo (`fundo.png`), a textura (`textura.png`), o logo e as medidas de cada linha (`medidas.js`).
