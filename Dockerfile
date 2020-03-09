FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

# prepare system
RUN apt-get update && apt-get install wget -y && wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo "deb https://debian.neo4j.com stable 3.5" > /etc/apt/sources.list.d/neo4j.list

RUN apt-get update && apt-get install git build-essential python3-dev python3-pip software-properties-common \
    openjdk-11-jre neo4j postgresql-server-dev-10 postgresql-plpython3-10 -y

# setup postgres
COPY postgres.conf /etc/postgresql/10/main/conf.d/cgrdb.conf
RUN service postgresql start && \
    sudo -u postgres psql --command "ALTER USER postgres WITH PASSWORD 'afirdb';" && \
    sudo -u postgres psql --command "CREATE SCHEMA reactions;"
RUN echo "PATH = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'" >> /etc/postgresql/10/main/environment

# setup neo4j
RUN neo4j-admin set-initial-password 'afirdb'

# install CGRdb
RUN git clone https://github.com/stsouko/smlar.git && \
    cd smlar && USE_PGXS=1 make && USE_PGXS=1 make install && cd .. & rm -rf smlar && \
    pip3 install compress-pickle git+https://github.com/cimm-kzn/CGRtools.git@master#egg=CGRtools[MRV] \
    git+https://github.com/stsouko/CIMtools.git@master#egg=CIMtools \
    git+https://github.com/stsouko/CGRdb.git@master#egg=CGRdb[postgres]

# setup CGRdb
COPY config.json config.json
RUN service postgresql start && cgrdb init -p afirdb && cgrdb create -p afirdb --name reactions --config config.json

# install AFIRdb
COPY AFIRdb .
RUN cd AFIRdb && pip3 install . && cd .. & rm -rf AFIRdb

# setup MarvinJS
COPY mjs /usr/local/lib/python3.6/dist-packages/AFIRdb/wui/assets/mjs
COPY boot.sh /opt/boot

VOLUME ["/var/log/postgresql", "/var/lib/postgresql"]
EXPOSE 5000

USER nouser
ENTRYPOINT ["/opt/boot"]
