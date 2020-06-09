FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

# prepare system
RUN apt-get update && apt-get install wget git build-essential python3-dev python3-pip software-properties-common \
    openjdk-11-jre postgresql-server-dev-10 postgresql-plpython3-10 ca-certificates -y

RUN wget -qO key "https://debian.neo4j.com/neotechnology.gpg.key"
RUN apt-key add key && rm key
RUN echo 'deb https://debian.neo4j.com stable 3.5' > /etc/apt/sources.list.d/neo4j.list

RUN apt-get update && apt-get install neo4j zip -y
RUN cd  /var/lib/neo4j/plugins/ && \
wget -q -O tmp.zip https://s3-eu-west-1.amazonaws.com/com.neo4j.graphalgorithms.dist/neo4j-graph-algorithms-3.5.14.0-standalone.zip && \
 unzip tmp.zip && rm tmp.zip
COPY neo4j.conf /etc/neo4j/neo4j.conf

# setup postgres
COPY postgres.conf /etc/postgresql/10/main/conf.d/cgrdb.conf
RUN echo "PATH = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'" >> /etc/postgresql/10/main/environment
USER postgres
RUN /etc/init.d/postgresql start && \
    psql --command "CREATE SCHEMA reactions;" && \
    psql --command "ALTER USER postgres WITH PASSWORD 'afirdb';"
USER root

# setup neo4j
RUN neo4j-admin set-initial-password 'afirdb'

# install CGRdb
RUN git clone https://github.com/stsouko/smlar.git && \
    cd smlar && USE_PGXS=1 make && USE_PGXS=1 make install && cd .. & rm -rf smlar && \
    pip3 install numba dash-uploader compress-pickle git+https://github.com/cimm-kzn/CGRtools.git@master#egg=CGRtools[clean2djit,MRV] \
    git+https://github.com/stsouko/CIMtools.git@master#egg=CIMtools \
    git+https://github.com/stsouko/CGRdb.git@master#egg=CGRdb[postgres]

# setup CGRdb
COPY config.json config.json
RUN service postgresql start && cgrdb init -p afirdb && cgrdb create -p afirdb --name reactions --config config.json && rm config.json

# install AFIRdb
COPY AFIRdb tmp/AFIRdb
COPY setup.py tmp/setup.py
COPY README.md tmp/README.md
COPY mol3d_dash-0.0.1-py3-none-any.whl tmp/mol3d_dash-0.0.1-py3-none-any.whl
COPY dash_network-0.0.1-py3-none-any.whl tmp/dash_network-0.0.1-py3-none-any.whl
RUN pip3 install /tmp/mol3d_dash-0.0.1-py3-none-any.whl && rm tmp/mol3d_dash-0.0.1-py3-none-any.whl
RUN pip3 install /tmp/dash_network-0.0.1-py3-none-any.whl && rm tmp/dash_network-0.0.1-py3-none-any.whl
RUN cd tmp && pip3 install . && rm -rf AFIRdb setup.py README.md && cd ..
RUN service neo4j start && sleep 10 && neomodel_install_labels AFIRdb AFIRdb.graph --db bolt://neo4j:afirdb@localhost:7687 && service neo4j stop
# setup MarvinJS
COPY mjs /usr/local/lib/python3.6/dist-packages/AFIRdb/wui/assets/mjs
COPY boot.sh /opt/boot

#VOLUME ["/var/log/postgresql", "/var/lib/postgresql"]
EXPOSE 5000

ENTRYPOINT ["/opt/boot"]
