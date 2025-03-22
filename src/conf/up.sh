docker build -t submissions ./src/submissions
docker build -t tasks ./src/tasks
docker build -t master ./src/master
docker build -t worker ./src/worker
docker compose -f src/conf/compose.yml up