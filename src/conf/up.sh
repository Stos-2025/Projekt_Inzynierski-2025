#!/bin/bash

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "WORKDIR: $WORKDIR"

docker build -f "$WORKDIR/src/master/dockerfile" -t stos_master "$WORKDIR/src"
docker build -f "$WORKDIR/src/worker/dockerfile" -t stos_worker "$WORKDIR/src"
docker build -f "$WORKDIR/src/adapter/dockerfile" -t stos_adapter "$WORKDIR/src"
docker compose -f "$WORKDIR/src/conf/compose.yml" up