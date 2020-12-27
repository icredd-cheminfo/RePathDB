#!/bin/bash
service postgresql start
service neo4j start
python3 -m RePathDB  -pg "//postgres:repathdb@localhost:5432/reactions" -nj "bolt://neo4j:repathdb@localhost:7687" wui -ls //0.0.0.0:5000
