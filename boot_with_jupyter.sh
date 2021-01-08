#!/bin/bash
service postgresql start
service neo4j start
sleep 10
cd examples && jupyter notebook --port 9999 --ip=0.0.0.0 --allow-root --NotebookApp.token='' --NotebookApp.password=''  2>&1 > /dev/null &
python3 -m RePathDB -pg "//postgres:repathdb@localhost:5432/reactions" -nj "bolt://neo4j:repathdb@localhost:7687" wui --debug -ls //0.0.0.0:5000
