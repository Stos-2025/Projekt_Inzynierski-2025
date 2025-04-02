docker build -t master ./src/master
docker build -t worker ./src/worker
docker build -t results ./src/results
docker compose -f src/conf/compose.yml up