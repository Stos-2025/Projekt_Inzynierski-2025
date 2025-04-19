docker build -t master ./src/master
docker build -t worker ./src/worker
docker build -t adapter ./src/adapter
docker compose -f src/conf/compose.yml up