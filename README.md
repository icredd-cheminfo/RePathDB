USAGE
=====

    python -m AFIRdb cmd
#initialization of TABLE in CGRDB 
cgrdb create -p '12345' --user USERNAME --port POSTGRES_PORT --host POSTGRES_HOST_IP  --name TABLE_NAME --config PATH_TO_CONFIG.JSON
#populate DB from log files
python -m AFIRdb -eq urea12_EQ_list.log -ts urea12_TS_list.log -pg POSTGRES_CONNECTION_INFO ("//user:port@host:port/table") \
-nj BOLT_CONNECTION_INFO"(bolt://login:pass@host:port") populate
#start WEB User Interface (wui)
python -m AFIRdb  -pg POSTGRES_CONNECTION_INFO("//user:port@host:port/table") -nj BOLT_CONNECTION_INFO("bolt://login:pass@host:port") wui -ls WEB_HOST

