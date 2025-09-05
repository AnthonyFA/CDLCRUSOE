#!/bin/bash

echo "Starting apache2" >> /var/log/entrypoint.log
service apache2 start
echo "apache2 Started" >> /var/log/entrypoint.log

echo "Starting neo4j" >> /var/log/entrypoint.log
neo4j-admin set-initial-password "${NEO4J_PASSWORD}"
service neo4j start

url='http://localhost:7474/user/neo4j/password'

json_body="{\"password\":\"${NEO4J_PASSWORD}\"}"

touch /var/log/entrypoint.log

echo "$(date) Waiting for neo4j to be available on port 7474" >> /var/log/entrypoint.log
while ! nc -z localhost 7474; do
    sleep 1
done
echo "$(date) neo4j available" >> /var/log/entrypoint.log

service supervisor start
echo "$(date) Waiting for neo4j to be available on port 7474" >> /var/log/entrypoint.log
service redis-server start

#curl -u neo4j:password -H "Content-Type: application/json" -X POST "${url}" -d "${json_body}" --trace-ascii -

#if [ $? -eq 0 ]; then
    #echo "$(date) Password change request sent successfully."
#else
    #echo "$(date) Failed to send password change request."
#fi

exec tail -f /dev/null