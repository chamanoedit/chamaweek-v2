# Fogo sobre o Altar — fonte das artes (4800×1350)

Tudo é gerado por código (Python + Chromium headless + ffmpeg): fogo procedural, brasas, fumaça,
grão de filme e tipografia. Todo movimento é periódico em 10 s, então os loops fecham sem emenda.

| Versão | Conceito | Tipografia |
|---|---|---|
| V1 | Referência à ID "Culto RGNR em Concerto": didone creme, retângulo dourado no "O", texto miúdo atrás do título, fogo desfocado, bokeh, luz âmbar e grão | Playfair (variável), Cinzel Decorative, Archivo |
| V2 | Altar de pedra com chifres e fogo vivo; "FOGO" ⟷ "SOBRE O ALTAR" ladeando o altar | Cinzel |
| V3 | Letras incandescentes com chamas saindo do topo e reflexo no chão | Anton, Archivo |

## Como renderizar de novo

```bash
pip install numpy opencv-python-headless scipy pillow   # + node com playwright e ffmpeg
FONTS_DIR=/tmp/fonts ./baixar_fontes.sh
export LAYERS=/tmp/layers FONTS_DIR=/tmp/fonts
python3 v1_text.py $LAYERS && python3 v2_text.py $LAYERS && python3 v3_text.py $LAYERS   # camadas de texto
python3 v1.py --scale 1 --still V1.png --t 7          # estático
python3 v1.py --scale 1 --video V1_loop.mp4           # loop 10 s / 30 fps
```

`--scale 0.25` gera prévias rápidas. Os textos ficam nos arquivos `v*_text.py`
(ex.: remover "CULTO RGNR EM CONCERTO" ou o versículo).
