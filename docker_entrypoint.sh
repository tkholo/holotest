echo "INIT top"
echo "INIT starting psql"
pg_ctlcluster 15 main start
sleep 20
echo "INIT startiung nginx"
service nginx start

export psql_db=h2
export psql_password=h2
export psql_port=5432
export psql_username=h2
export psql_hostname=localhost

echo "INIT starting wsgi server"
/etc/init.d/holo_wsgi start
echo "INIT wsgi started"

##test
echo "pg test"
PGPASSWORD=h2 psql -h localhost -d h2 -U h2 -c "SELECT datname FROM pg_catalog.pg_database"
echo "pg test complete"

#might also turn off logger line from wsgi and go back to the sleep infinity
#touch /tmp/uwsgi.log
while :
do
	tail -f --retry /tmp/uwsgi.log /var/log/nginx/*
	echo "INIT waiting for log:"
	sleep 5
	#ls -laF /tmp/
	#tail /var/log/nginx/*
done
