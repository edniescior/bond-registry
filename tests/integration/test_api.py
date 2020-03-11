import requests
import json
from boto3.dynamodb.conditions import Key

"""
Integration tests against the bond registry api. These tests execute
against docker containers.

Fixtures to start containers, build the dynamodb table and populate it
with test data are in conftest.py.
"""


def test_health(api_url, table):
    """
    The fixtures will guarantee that the containers are up. We should
    get a healthy response from the API.
    """
    response = requests.get(f"http://{api_url}/health_check")
    assert response.status_code == 200, "API did not start correctly"


def test_create_bond(api_url, table):
    """
    Create a new bond. The bond object is returned.
    """
    bond = {
        "bond_id": "foo123",
        "host_account_id": "EHFW8W88",
        "sub_account_id": "IU2I83IW",
        "host_cost_center": "teal",
        "sub_cost_center": "green",
        "subscribers": {
            "bob": {
                "sid": "bob",
                "name": "Bob",
                "email": "bob@bobiverse.com"
            }
        }
    }
    response = requests.post(f"http://{api_url}/bonds/", data=json.dumps(bond))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert response_body['bond_id'] == "foo123"
    assert response_body['host_account_id'] == "EHFW8W88"
    assert response_body['sub_account_id'] == "IU2I83IW"
    assert response_body['host_cost_center'] == "teal"
    assert response_body['sub_cost_center'] == "green"
    assert response_body['subscribers']['bob']['sid'] == "bob"
    assert response_body['subscribers']['bob']['name'] == "Bob"
    assert response_body['subscribers']['bob']['email'] == "bob@bobiverse.com"

    result_set = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('foo123')
    )

    # Check the backend db
    assert result_set.get("Count") == 1
    items = result_set.get("Items")
    assert items[0]["bond_id"] == 'foo123'
    assert items[0]["host_account_id"] == 'EHFW8W88'
    assert items[0]["sub_account_id"] == 'IU2I83IW'
    assert items[0]["host_cost_center"] == 'teal'
    assert items[0]["sub_cost_center"] == 'green'
    subs = items[0]["subscribers"]
    assert len(subs) == 1
    assert subs['bob']['sid'] == 'bob'
    assert subs['bob']['name'] == 'Bob'
    assert subs['bob']['email'] == 'bob@bobiverse.com'


def test_create_bond_exists(api_url, table):
    """
    Try to create a bond that already exists. A 400 error is returned
    with an appropriate message.
    """
    bond = {
        "bond_id": "6cc333cd",
        "host_account_id": "KYOT95889719595091",
        "sub_account_id": "NSSV61341208978885",
        "host_cost_center": "yellow",
        "sub_cost_center": "silver",
        "subscribers": {}
    }
    response = requests.post(f"http://{api_url}/bonds/", data=json.dumps(bond))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 400
    response_body = response.json()
    assert response_body['detail'] == "Bond already exists: bond_id=" \
                                      "6cc333cd"


def test_create_bond_malformed(api_url, table):
    """
    Pass in some malformed JSON. Returns a 422 error with an appropriate
    message.
    """
    bond = {
        "bond_id": "bar123",
        "host_account_id": "EHFW8W88",
        "sub_account_id": "IU2I83IW",
        "host_cost_center": "teal",
        "sub_cost_center": "green",
        "subscribers": {
            "bob": {
                "sid": "bob",
                "name": "Bob",
                "email": "malformedemail"
            }
        }
    }
    response = requests.post(f"http://{api_url}/bonds/", data=json.dumps(bond))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 422
    response_body = response.json()
    assert response_body['detail'][0]['msg'] == "value is not a valid email " \
                                                "address"
    assert response_body['detail'][0]['type'] == "value_error.email"


def test_update_bond_not_exists(api_url, table):
    """
    Attempting to update a bond that doesn't exist will raise a 400 error.
    """
    bond = {
        "bond_id": "bar123",
        "host_account_id": "EHFW8W88",
        "sub_account_id": "IU2I83IW",
        "host_cost_center": "teal",
        "sub_cost_center": "green",
        "subscribers": {
            "bob": {
                "sid": "bob",
                "name": "Bob",
                "email": "bob@bobiverse.com"
            }
        }
    }
    response = requests.put(f"http://{api_url}/bonds/bar123", data=json.dumps(
        bond))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 400
    response_body = response.json()
    assert response_body['detail'] == "Bond bar123 not found."


def test_update_bond(api_url, table):
    """
    Updating a bond will return the updated bond. Check the backend also.
    """
    bond = {
        "bond_id": "6cc333cd",
        "host_account_id": "KYOT95889719595091",
        "sub_account_id": "NSSV61341208978885",
        "host_cost_center": "yellow",
        "sub_cost_center": "brown",
        "subscribers": {
            "fred": {
                "sid": "fred",
                "name": "Fred",
                "email": "fred@flub.com"
            }
        }
    }
    response = requests.put(f"http://{api_url}/bonds/6cc333cd",
                            data=json.dumps(bond))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert response_body['bond_id'] == "6cc333cd"
    assert response_body['host_account_id'] == "KYOT95889719595091"
    assert response_body['sub_account_id'] == "NSSV61341208978885"
    assert response_body['host_cost_center'] == "yellow"
    assert response_body['sub_cost_center'] == "brown"
    assert response_body['subscribers']['fred']['sid'] == "fred"
    assert response_body['subscribers']['fred']['name'] == "Fred"
    assert response_body['subscribers']['fred']['email'] == "fred@flub.com"

    result_set = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('6cc333cd')
    )

    # Check the backend db
    assert result_set.get("Count") == 1
    items = result_set.get("Items")
    assert items[0]["bond_id"] == '6cc333cd'
    assert items[0]["host_account_id"] == 'KYOT95889719595091'
    assert items[0]["sub_account_id"] == 'NSSV61341208978885'
    assert items[0]["host_cost_center"] == 'yellow'
    assert items[0]["sub_cost_center"] == 'brown'
    subs = items[0]["subscribers"]
    assert len(subs) == 1
    assert subs['fred']['sid'] == 'fred'
    assert subs['fred']['name'] == 'Fred'
    assert subs['fred']['email'] == 'fred@flub.com'


def test_add_subscriber_bond_not_exists(api_url, table):
    """
    Attempting to add a subscriber to a bond that doesn't exist will
    raise a 400 error.
    """
    sub = {
        "sid": "barb",
        "name": "Barb",
        "email": "barb@rella.com"
    }
    response = requests.post(f"http://{api_url}/bonds/bar234/subscribers",
                             data=json.dumps(sub))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 400
    response_body = response.json()
    assert response_body['detail'] == "Bond bar234 not found. Cannot add " \
                                      "subscriber barb."


def test_add_subscriber(api_url, table):
    """
    Adding a subscriber will return the updated bond. Check the backend
    db also.
    """
    sub = {
        "sid": "barb",
        "name": "Barb",
        "email": "barb@rella.com"
    }
    response = requests.post(f"http://{api_url}/bonds/bf66a510/subscribers",
                             data=json.dumps(sub))
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert response_body['bond_id'] == "bf66a510"
    assert response_body['host_account_id'] == "HAEP29388232018739"
    assert response_body['sub_account_id'] == "WZNH57184416064999"
    assert response_body['host_cost_center'] == "yellow"
    assert response_body['sub_cost_center'] == "white"
    assert response_body['subscribers']['barb']['sid'] == "barb"
    assert response_body['subscribers']['barb']['name'] == "Barb"
    assert response_body['subscribers']['barb']['email'] == "barb@rella.com"

    result_set = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('bf66a510')
    )

    # Check the backend db
    assert result_set.get("Count") == 1
    items = result_set.get("Items")
    assert items[0]["bond_id"] == 'bf66a510'
    assert items[0]["host_account_id"] == 'HAEP29388232018739'
    assert items[0]["sub_account_id"] == 'WZNH57184416064999'
    assert items[0]["host_cost_center"] == 'yellow'
    assert items[0]["sub_cost_center"] == 'white'
    subs = items[0]["subscribers"]
    assert len(subs) == 4
    assert subs['barb']['sid'] == 'barb'
    assert subs['barb']['name'] == 'Barb'
    assert subs['barb']['email'] == 'barb@rella.com'


def test_remove_subscriber_bond_not_exists(api_url, table):
    """
    Attempting to remove a subscriber from a bond that doesn't exist will
    raise a 400 error.
    """
    response = requests.delete(f"http://{api_url}/bonds/bar345/subscribers/a")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 400
    response_body = response.json()
    assert response_body['detail'] == "Bond bar345 not found. Cannot remove " \
                                      "subscriber a."


def test_remove_subscriber(api_url, table):
    """
    Removing a subscriber will return the updated bond. Check the backend
    db also.
    """
    response = requests.delete(f"http://{api_url}/bonds/"
                               f"3f4436a3/subscribers/tfomoo100")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert response_body['bond_id'] == "3f4436a3"
    assert response_body['host_account_id'] == "BULG01950964065116"
    assert response_body['sub_account_id'] == "PFUP24464317335973"
    assert response_body['host_cost_center'] == "maroon"
    assert response_body['sub_cost_center'] == "navy"
    assert response_body['subscribers']['eniesc200']['sid'] == "eniesc200"
    assert response_body['subscribers']['bfoere300']['sid'] == "bfoere300"

    result_set = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('3f4436a3')
    )

    # Check the backend db
    assert result_set.get("Count") == 1
    items = result_set.get("Items")
    assert items[0]["bond_id"] == '3f4436a3'
    assert items[0]["host_account_id"] == 'BULG01950964065116'
    assert items[0]["sub_account_id"] == 'PFUP24464317335973'
    assert items[0]["host_cost_center"] == 'maroon'
    assert items[0]["sub_cost_center"] == 'navy'
    subs = items[0]["subscribers"]
    assert len(subs) == 2
    assert subs['eniesc200']['sid'] == 'eniesc200'
    assert subs['bfoere300']['sid'] == 'bfoere300'


def test_delete_bond_not_exists(api_url, table):
    """
    Attempting to delete a bond that doesn't exist will do nothing.
    A 200 code will be returned.
    """
    response = requests.delete(f"http://{api_url}/bonds/bar456")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200


def test_delete_bond(api_url, table):
    """
    Deleting a bond will return a 200 code regardless. Check the backend
    db to be sure the bond is gone.
    """
    response = requests.delete(f"http://{api_url}/bonds/deleteme")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    result_set = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('deleteme')
    )

    # Check the backend db
    assert result_set.get("Count") == 0


def test_get_bond_not_found(api_url, table):
    """
    Attempt to get a bond that doesn't exist. Returns a 400 and the
    appropriate message.
    """
    response = requests.get(f"http://{api_url}/bonds/foo")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 400
    response_body = response.json()
    assert response_body['detail'] == "Bond foo not found."


def test_get_bond(api_url, table):
    """
    Fetch a specific bond. The bond is returned.
    """
    response = requests.get(f"http://{api_url}/bonds/e6d9c05f")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert response_body['bond_id'] == "e6d9c05f"
    assert response_body['host_account_id'] == "YHRH31548177246824"
    assert response_body['sub_account_id'] == "QZUL57771567168857"
    assert response_body['host_cost_center'] == "navy"
    assert response_body['sub_cost_center'] == "aqua"
    assert response_body['subscribers']['eniesc200']['sid'] == "eniesc200"
    assert response_body['subscribers']['eniesc200']['name'] == "Ed"
    assert response_body['subscribers']['eniesc200']['email'] == "ed@mail.com"
    assert response_body['subscribers']['tfomoo100']['sid'] == "tfomoo100"
    assert response_body['subscribers']['tfomoo100']['name'] == "Tom"
    assert response_body['subscribers']['tfomoo100']['email'] == \
        "tom@snail.com"
    assert response_body['subscribers']['bfoere300']['sid'] == "bfoere300"
    assert response_body['subscribers']['bfoere300']['name'] == "Bill"
    assert response_body['subscribers']['bfoere300']['email'] == \
        "bill@mojo.com"


def test_get_bonds_not_found(api_url, table):
    """
    Fetching on a bogus cost center will return an empty list.
    """
    response = requests.get(f"http://{api_url}/bonds"
                            f"?cost_center_id=apple&by_host=true")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert response_body == []


def test_get_bonds_by_host_cost_center(api_url, table):
    """
    Get all bonds for a specific host cost center.
    """
    response = requests.get(f"http://{api_url}/bonds"
                            f"?cost_center_id=maroon&by_host=true")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]['bond_id'] == '3f4436a3'
    assert response_body[1]['bond_id'] == '070840c5'


def test_get_bonds_by_host_account_id(api_url, table):
    """
    Get all bonds for a specific host account id.
    """
    response = requests.get(f"http://{api_url}/bonds"
                            f"?account_id=YHRH31548177246824&by_host=true")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]['bond_id'] == 'e6d9c05f'
    assert response_body[1]['bond_id'] == 'eb5e729a'


def test_get_bonds_by_sub_cost_center(api_url, table):
    """
    Get all bonds for a specific subscriber cost center.
    """
    response = requests.get(f"http://{api_url}/bonds"
                            f"?cost_center_id=orange&by_host=false")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert len(response_body) == 3
    assert response_body[0]['bond_id'] == 'eb5e729a'
    assert response_body[1]['bond_id'] == '2e545043'
    assert response_body[2]['bond_id'] == '402206d5'


def test_get_bonds_by_sub_account_id(api_url, table):
    """
    Get all bonds for a specific subscriber account id.
    """
    response = requests.get(f"http://{api_url}/bonds"
                            f"?account_id=CNUE67550266655258&by_host=false")
    assert response.headers['Content-Type'] == "application/json"
    assert response.status_code == 200

    # Check the API response body
    response_body = response.json()
    assert len(response_body) == 1
    assert response_body[0]['bond_id'] == '402206d5'
