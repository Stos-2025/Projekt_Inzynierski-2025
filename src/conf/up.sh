#!/bin/bash

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "WORKDIR: $WORKDIR"

docker build -f "$WORKDIR/src/master/dockerfile" -t master "$WORKDIR/src"
docker build -f "$WORKDIR/src/worker/dockerfile" -t worker "$WORKDIR/src"
docker build -f "$WORKDIR/src/adapter/dockerfile" -t adapter "$WORKDIR/src"
docker compose -f "$WORKDIR/src/conf/compose.yml" up