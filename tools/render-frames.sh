#!/bin/sh
# Render the rotating-view frames inside one kicad-cli environment.
# Usage: render-frames.sh DIR STEP SIZE ZOOM   (DIR/board.kicad_pcb in, DIR/frameNNN.png out)
set -e
dir=$1 step=${2:?step} size=${3:?size} zoom=${4:?zoom}
cli=${KICAD_CLI:-kicad-cli}
total=$(seq 0 "$step" 359 | wc -l | tr -d " ")
i=0
for angle in $(seq 0 "$step" 359); do
  [ $((i % 10)) -eq 0 ] && echo "render: frame $i/$total"
  $cli pcb render --width "$size" --height "$size" --zoom "$zoom" --background transparent \
    --rotate "0,-$angle,45" -o "$dir/$(printf 'frame%03d' $i).png" "$dir/board.kicad_pcb" >/dev/null
  i=$((i + 1))
done
