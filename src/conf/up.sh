docker build -f src/master/dockerfile -t master ./src
docker build -f src/worker/dockerfile -t worker ./src
docker build -f src/adapter/dockerfile -t adapter ./src
docker compose -f src/conf/compose.yml up