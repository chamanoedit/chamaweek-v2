#!/usr/bin/env bash
# Baixa as fontes (Google Fonts, licença OFL) usadas nas artes.
set -e
DEST="${FONTS_DIR:-/tmp/fonts}"; mkdir -p "$DEST"; cd "$DEST"
B=https://raw.githubusercontent.com/google/fonts/main/ofl
for f in "playfair/Playfair%5Bopsz,wdth,wght%5D.ttf" "cinzeldecorative/CinzelDecorative-Regular.ttf" \
         "cinzeldecorative/CinzelDecorative-Bold.ttf" "cinzel/Cinzel%5Bwght%5D.ttf" "archivo/Archivo%5Bwdth,wght%5D.ttf" \
         "anton/Anton-Regular.ttf" "cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf"; do
  out=$(basename "$f" | sed 's/%5B/[/g; s/%5D/]/g'); curl -sSf -o "$out" "$B/$f" && echo "ok $out"
done
