#!/bin/bash
service postgresql start
service neo4j start
python3 -m AFIRdb  -pg "//postgres:afirdb@localhost:5432/reactions" -nj "bolt://neo4j:afirdb@localhost:7687" wui
