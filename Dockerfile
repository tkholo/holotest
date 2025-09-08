FROM python:3.10-slim-bookworm

RUN apt-get update \
    && apt-get install -y curl wget postgresql postgresql-contrib postgresql-client gcc libpq-dev nginx sudo wamerican vim

#these should use specific versions or a requirements.txt
RUN python3 -m pip install psycopg2 uwsgi requests

#
#{
#"id": 7294,
#"mnc": 182,
#"bytes_used": 293451,
#"dmcc": null,
#"cellid": 31194,
#"ip": "192.168.0.1"
#},

RUN echo "CREATING pg holo TABLES" \
    && pg_ctlcluster 15 main start \
    #&& echo "PSQL CONF FILE xx:" \
    && sudo -u postgres psql -c 'SHOW config_file' \
    #&& ls -laF /etc/postgresql/11/main/postgresql.conf \
    #&& grep synchronous_commit /etc/postgresql/11/main/postgresql.conf \
    #&& grep wal_writer_delay /etc/postgresql/11/main/postgresql.conf \
    #&& grep enable_seqscan /etc/postgresql/11/main/postgresql.conf \
    && echo "creating dbs and users" \
    && sudo -u postgres psql -c "CREATE USER h2 WITH ENCRYPTED PASSWORD 'h2'" \
    && sudo -u postgres psql -c "CREATE DATABASE h2" \
    && sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE h2 TO h2" \
    && sudo -u postgres psql -d h2 -c "GRANT CREATE ON SCHEMA public TO h2" \
    #&& echo "calling senzing db setups" \
    && export PGPASSWORD=h2 \
    && echo "check resulting dbs" \
    #&& psql -h localhost -d h2 -U h2 -p 5432 -c   \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE TABLE cdr_data (  \
    	uid BIGSERIAL,  \
	file_id BIGINT NOT NULL,  \
	cdr_id BIGINT NOT NULL,  \
	mnc INT,  \
	bytes_used INT NOT NULL,  \
	cell_id INT,  \
	ip VARCHAR(20),  \
	dmcc VARCHAR(256)  \
        ) " \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE TABLE cdr_file (  \
        file_id BIGINT NOT NULL,  \
	file_name VARCHAR(200) NOT NULL,  \
	tstamp TIMESTAMP  \
        ) " \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE TABLE errors ( \
        file_id BIGINT NOT NULL, \
	raw_text VARCHAR(200) NOT NULL, \
	err_msg VARCHAR(200) NOT NULL \
	) " \
    && echo "create indexes" \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE INDEX ON cdr_data (cdr_id)" \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE INDEX ON cdr_data (file_id)" \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE INDEX ON cdr_file (file_id)" \
    && psql -h localhost -d h2 -U h2 -p 5432 -c "CREATE INDEX ON errors (file_id)" \
    && sudo -u postgres psql -c "SELECT datname FROM pg_catalog.pg_database" \
    && echo "dbs" \
    && pg_ctlcluster 15 main stop


SHELL ["/bin/bash", "-c"]

RUN mkdir /opt/data

COPY nginx/default /etc/nginx/sites-enabled/
COPY nginx/index.html /var/www/html/
COPY nginx/holo_wsgi /etc/init.d/
COPY nginx/generate_test_data.py /var/www/wsgi/
COPY nginx/cdr_ops.py /var/www/wsgi/
COPY nginx/holo.ini  /var/www/wsgi/
COPY nginx/holo.py   /var/www/wsgi/
COPY nginx/mysd.py   /var/www/wsgi/
COPY nginx/test_data_err_20.txt /opt/data
COPY nginx/test_file_upload.sh /opt/data
COPY nginx/test_get_data.sh /opt/data
COPY nginx/test_get_errors.sh /opt/data
RUN  adduser --quiet --no-create-home --disabled-password --gecos "" holo \
    && chown -R holo:www-data /var/www/wsgi/ \
    && chmod 777 /var/www/wsgi \
    && chmod 755 /etc/init.d/holo_wsgi \
    && ls -laF /var/www/wsgi

RUN echo "RUNNING TESTS" \
    && service nginx start \
    && pg_ctlcluster 15 main start \
    && echo "setupenv:" \
    && export psql_db=h2 \
    && export psql_password=h2 \
    && export psql_port=5432 \
    && export psql_username=h2 \
    && export psql_hostname=localhost \ 
    && /etc/init.d/holo_wsgi start \
    && ls -laF / \
    && ls -laF /tmp/ \
    && ls -laF /var/www/wsgi \
    && ls -laF /run \
    && ls -laF /var/log/ \
    && ls -laF /var/log/nginx/ \
    && cat /var/log/nginx/error.log \
    && cat /run/holo.pid \
    #REQUIRES procps package && /bin/ps eax |grep `cat /run/holo.pid` \
    #REQUIRES procps package && /bin/ps eax |grep wsgi \
    && sleep 10 \
    && export PGPASSWORD=h2 \
    && python /var/www/wsgi/generate_test_data.py test_1000 1000 \
    && python /var/www/wsgi/holo.py test_1000 \
    && bash /opt/data/test_file_upload.sh /opt/data/test_data_err_20.txt \
    && bash /opt/data/test_file_upload.sh test_1000 \
    && bash /opt/data/test_get_data.sh \
    && bash /opt/data/test_get_errors.sh \
    #&& wget --tries=1 --post-data '{"cmd":"get_all_data","parms":{}}' http://localhost/holo -O /tmp/holo1 || : \
    && curl -X POST  -F "cmd=get_all_data"  http://localhost/holo \
    && echo "test complete, reverting tables" \
    && curl -X POST  -F "cmd=delete_all_data"  http://localhost/holo \
    && echo "wgets done" \
    #&& cat /tmp/holo1 \
    #&& cat /tmp/holo2 \
    && cat /var/log/nginx/error.log \
    && cat /var/log/nginx/access.log \
    && echo "UWSGI LOG:" \ 
    && ls -laF /tmp/ \
    && cat /tmp/*.log \
    && find /var -type s |grep sock || :



    

COPY docker_entrypoint.sh /opt/
CMD [ "/bin/bash", "/opt/docker_entrypoint.sh" ]

