#!/bin/bash
# Render a PPTX to per-slide PNGs. Usage: ./render.sh file.pptx outdir
set -e
PPTX="$1"
OUT="${2:-previews}"
SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
rm -rf "$OUT" && mkdir -p "$OUT"
WORK=$(mktemp -d)
"$SOFFICE" --headless --convert-to pdf --outdir "$WORK" "$PPTX" >/dev/null 2>&1
PDF="$WORK/$(basename "${PPTX%.pptx}").pdf"
pdftoppm -png -r 110 "$PDF" "$OUT/s" >/dev/null 2>&1
cd "$OUT"
for f in s-*.png; do
  n=$(echo "$f" | sed -E 's/s-0*([0-9]+)\.png/\1/')
  nn=$(printf "%02d" "$((10#$n))")
  mv "$f" "slide_$nn.png"
done
cd - >/dev/null
rm -rf "$WORK"
echo "Rendered $(ls "$OUT" | wc -l | tr -d ' ') slides to $OUT/"
