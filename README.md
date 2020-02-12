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

## Setting Up

Create a Python virtual environment on your local machine. For example, if you
are using venv, run the following from the top-level project directory:

To create the environment: ```$ python3 -m venv .venv```

To activate it: ```$ source .venv/bin/activate```

To deactivate it: ```$ deactivate```

To install the packages needed, run: ```$ pip install -r requirements.txt```

## Testing
### Unit Tests

To run unit tests execute: ```$ python -m pytest tests/unit/test_*```

To test PEP8 compliance, run:
```shell script
$ pycodestyle --show-source --show-pep8 registry/ tests/
```

## Running locally

To start the server: ```$ uvicorn registry.main:app --reload```

To access the OpenAPI docs open: http://localhost:8000/docs
