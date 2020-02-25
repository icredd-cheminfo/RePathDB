USAGE
=====

    python -m AFIRdb cmd
#initialization of TABLE in CGRDB 
cgrdb create -p '12345' --user postgres --port 54320 --host 133.87.242.108  --name reactions --config CGRDBTutorial/config.json
python -m AFIRdb -eq urea12_EQ_list.log -ts urea12_TS_list.log -pg "//postgres:12345@localhost:54320/reactions" -nj "bolt://neo4j:12345@localhost:7687"

