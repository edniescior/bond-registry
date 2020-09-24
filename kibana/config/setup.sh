#!/usr/bin/env bash
##!/usr/bin/env bash

# Create the index pattern in Kibana
echo "Waiting for Kibana ..."
sleep 30

# it takes a while for Kibana to start up, so put in a retry loop to poll it.
retries=5
wait_retry=10
command="curl -i http://localhost:5601/api/status"

for i in `seq 1 $retries`; do
    $command
    ret_value=$?
    [ $ret_value -eq 0 ] && break
    echo "> Failed attempt $i of $retries, waiting to retry..."
    sleep $wait_retry
done

echo
echo
echo "Creating the Filebeat index pattern."
curl \
-X POST "http://localhost:5601/api/saved_objects/index-pattern/filebeat" \
 -H 'kbn-xsrf: true' \
 -H 'Content-Type: application/json' \
 --data-binary @- << EOF
{
    "attributes": {
        "title": "filebeat-*",
        "timeFieldName": "@timestamp"
    }
}
EOF
