#!/bin/sh
# Render the rotating-view frames inside one kicad-cli environment.
# Usage: render-frames.sh DIR   (DIR/board.kicad_pcb in, DIR/frameNNN.png out)
set -e
dir=$1
cli=${KICAD_CLI:-kicad-cli}
i=0
for angle in $(seq 0 3 357); do
  [ $((i % 10)) -eq 0 ] && echo "render: frame $i/120"
  $cli pcb render --width 400 --height 400 --zoom 0.7 --background opaque \
    --rotate "0,-$angle,45" -o "$dir/$(printf 'frame%03d' $i).png" "$dir/board.kicad_pcb" >/dev/null
  i=$((i + 1))
done
