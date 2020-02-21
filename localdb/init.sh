#!/bin/sh

# The AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars are set for every
# command. This is because I want to ensure that my local global version of
# these env vars (which are pointed at my own private AWS account) are not used.

echo "Deleting any pre-existing tables\n"
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb delete-table \
	--table-name bond \
	--endpoint-url http://0.0.0.0:8000 \
	--region us-west-2

echo "Creating bond table\n"
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb create-table \
	--cli-input-json "$(cat 01-create-table.json)" \
	--endpoint-url http://0.0.0.0:8000 \
	--region us-west-2

echo "Loading data into bond table\n"
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb batch-write-item \
	--request-items "$(cat 02-load-data.json)" \
	--endpoint-url http://0.0.0.0:8000 \
	--region us-west-2

echo "Query just to ensure that everything has worked as expected\n"
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb query \
    --table-name bond \
    --key-condition-expression "bond_id = :v1" \
    --expression-attribute-values "{ \":v1\" : { \"S\" : \"TEST007\" } }" \
	--endpoint-url http://0.0.0.0:8000 --region us-west-2

 # AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
 # AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
 # aws dynamodb scan --table-name "bond" \
 #     --endpoint-url http://localhost:8000 --region us-west-2