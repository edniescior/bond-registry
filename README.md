# Bond Registry Service

This is a reference implementation of a simple registry service that allows for
the creation, retrieval, update and deletion of *bonds*. A bond represents a
relationship between two parties (*accounts*) whereby one party (the subscriber
account) promises to pay the other (the host account) for services provided by
the host. It is shorthand for a 'charge-back relationship'.

The finished project will be a Python API (built on FastAPI) running in a
Docker container that speaks to Dynamodb as the back end.

## The Data
The natural key for a bond is a composite of host account id and subscriber
account id.

A *cost center* represents a funding entity and is used to group accounts.
There is a one-to-many relationship between cost centers and accounts. Host and
subscriber accounts may belong to the same cost center.

Each bond maintains a collection of *subscribers*. These are individuals who
are affiliated with the subscriber account and are authorized, based on the
bond, to request services from the host account.

The data model looks something like this:

```json
{
  "bond_id": "ID007",
  "host_account_id": "QYSS37952707405491",
  "sub_account_id": "SQSY48031267772693",
  "host_cost_center": "teal",
  "sub_cost_center": "yellow",
  "subscribers": {
    "rharper": {
      "sid": "rharper",
      "name": "Richard Harper",
      "email": "richharper@gmail.com"
    },
    "rlarson": {
      "sid": "rlarson",
      "name": "Rachel Larson",
      "email": "r.larson@gmail.com"
    },
    "kathill": {
      "sid": "kathill",
      "name": "Kathryn Hill",
      "email": "khill04@yahoo.com"
    }
  }
}
```

## Pre-requisites
```
Docker
AWS CLI
```

## Running It Locally

The amazon/dynamodb-local image has been added to `docker-compose.yml`

In production, the DynamoDB table will have been created via Terraform, so
our code will expect a table to be there already. Locally, I will run a shell
script once the container has been brought up to create the table and populate 
it with some test data.

The directory structure for all this looks like this:

```
localdb
    |-- 01-create-table.json
    |-- 02-load-data.json
    |-- init.sh
```
* `01-create-table.json` This file creates a table called 'bond' in DynamoDB.
* `02-load-data.json` This will load dummy data into DynamoDB.
* `init.sh` Runs some AWS CLI commands and uses the above files as input.

I bring up the container via a Makefile with `make init`.

Which should give us:
```
$ docker-compose ps
     Name                   Command               State           Ports         
--------------------------------------------------------------------------------
bond-registry    /start.sh                        Up      80/tcp, 0.0.0.0:5000->8080/tcp
dynamodb-local   java -jar DynamoDBLocal.ja ...   Up      0.0.0.0:8000->8000/tcp  
```

Testing it via curl should give us: `curl -X GET "http://localhost:5000/bonds/TEST007" -H "accept: application/json"`

```json
{ 
   "bond_id":"TEST007",
   "host_account_id":"QIOK20853445912302",
   "sub_account_id":"KMMI39246229932687",
   "host_cost_center":"gray",
   "sub_cost_center":"olive",
   "subscribers":{ 
      "gregorykeller":{ 
         "sid":"gregorykeller",
         "name":"Troy Nolan",
         "email":"kellyjohnson@gmail.com"
      },
      "qking":{ 
         "sid":"qking",
         "name":"Brian Schneider",
         "email":"sullivanangela@hotmail.com"
      },
      "cooperchristina":{ 
         "sid":"cooperchristina",
         "name":"James Nash",
         "email":"jenniferklein@yahoo.com"
      }
   }
}
```
I can view the OpenAPI docs at `http://localhost:5000/docs`.

I tail the server logs with `docker logs --follow bond-registry`.

I bring it all down with `docker-compose down`.

### (Optional) Running Some Queries Against the Local DynamoDB Instance
Here are some queries to play with the local DynamoDB environment:

_(Note: The AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars are set for
    every command. This is because I want to ensure my local global version
    of these env vars (which are pointed at my own private AWS account)
    are not used.)_

#### Describe the bond table
```
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb describe-table \
    --table-name bond \
	--endpoint-url http://0.0.0.0:8000 --region us-west-2
```

#### Get me a specific record
```
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb query \
    --table-name bond \
    --key-condition-expression "bond_id = :v1" \
    --expression-attribute-values "{ \":v1\" : { \"S\" : \"TEST007\" } }" \
	--endpoint-url http://0.0.0.0:8000 --region us-west-2
```

#### List the entire contents of the table
```
AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY \
aws dynamodb scan \
    --table-name bond \
	--endpoint-url http://0.0.0.0:8000 --region us-west-2
```


## Development

Create a Python virtual environment on your local machine. For example, if you
are using venv, run the following from the top-level project directory:

To create the environment: ```python3 -m venv .venv```

To activate it: ```source .venv/bin/activate```

To deactivate it: ```deactivate```

To install the packages needed, run: ```pip install -r requirements.txt```

## Testing
### Unit Tests

To run unit tests execute: ```python -m pytest tests/unit/test_*```

To test PEP8 compliance, run:
```shell script
pycodestyle --show-source --show-pep8 registry/ tests/
```
