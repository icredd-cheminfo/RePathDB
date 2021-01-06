#!/bin/bash
service postgresql start
service neo4j start
sleep 1
python3 -m RePathDB  -pg "//postgres:repathdb@localhost:5432/reactions" -nj "bolt://neo4j:repathdb@localhost:7687" wui --debug -ls //0.0.0.0:5000
