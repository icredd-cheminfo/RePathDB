BEFORE INSTALLATION
=====
Download Marvin JS from ChemAxon site https://chemaxon.com/products/marvin-js/download

Click Download Packaged Archive

extract it as mjs and put into project directory

DOCKER INSTALLATION
=====
docker build -f Dockerfile_with_jupyter . -t repathdb:jupyter

docker run -d -p 5432:5432 -p 5000:5000 -p 7474:7474 -p 7687:7687 -p 9999:9999 repathdb:jupyter

port 5432 for postgres connections

port 5000 for RePathDB visualisation

port 7474 for web interface of neo4j

port 7687 for bolt connection of neo4j

port 9999 for jupyter connection

INSTALLATION on the system (not recomended)
=====

Install last version of neo4j 3 and postgres 10

Create virtual environment, activate it and install dash_network and mol3d_dash wheels

Then run pip install -e .  in the folder of the project 

USAGE
=====

    python -m RePathDB cmd
#initialization of CGRDB  
    cgrdb init  -c '{"user":"your postgres user name","password":"your password","host":"host ip"}'

#creation of table in the CGRDB
    cgrdb create -n "reactions" -f config.json -c '{"user":"your postgres user name","password":"your password","host":"host ip"}'

# creations of labels in NEO4J
    neomodel_install_labels RePathDB RePathDB.graph --db bolt://login:pass@host:port
#populate DB from log files (please be sure that you added your own parser to process your files)

    python -m RePathDB -f "your folder" -s "files extension" -pg POSTGRES_CONNECTION_INFO ("//user:port@host:port/table") \
    -nj BOLT_CONNECTION_INFO"(bolt://login:pass@host:port") populate
#start WEB User Interface (wui)
    python -m RePathDB  -pg POSTGRES_CONNECTION_INFO("//user:pass@host:port/table") -nj BOLT_CONNECTION_INFO("bolt://login:pass@host:port") wui -ls WEB_HOST


