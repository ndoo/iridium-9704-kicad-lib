#!/bin/sh
# Run kicad-cli from the official KiCad Docker image. The working directory is mounted at
# the same path, so relative and absolute paths under it work unchanged.
# KICAD_DOCKER_PLATFORM=linux/amd64 selects the image architecture on arm64 hosts.
exec docker run --rm ${KICAD_DOCKER_PLATFORM:+--platform "$KICAD_DOCKER_PLATFORM"} \
  --user "$(id -u):$(id -g)" -e HOME=/tmp -e IRIDIUM_9704_3DMODEL_DIR \
  -v "$PWD:$PWD" -w "$PWD" "${KICAD_IMAGE:-kicad/kicad:10.0}" kicad-cli "$@"
