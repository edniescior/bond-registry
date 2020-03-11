import pytest
import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
from fastapi.encoders import jsonable_encoder

from registry.models import Bond, Subscriber
from registry.db import ConditionalCheckError
from registry import crud


@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope='function')
def dynamodb(aws_credentials):
    with mock_dynamodb2():
        yield boto3.resource('dynamodb', region_name='us-east-1')


@pytest.fixture(scope='function')
def table(dynamodb):
    """Create the mock bond table."""
    with open("./localdb/01-create-table.json") as read_file:
        table_def = json.load(read_file)
    table = dynamodb.create_table(
        TableName=table_def['TableName'],
        BillingMode=table_def['BillingMode'],
        KeySchema=table_def['KeySchema'],
        AttributeDefinitions=table_def['AttributeDefinitions'],
        GlobalSecondaryIndexes=table_def['GlobalSecondaryIndexes'])
    yield table


@pytest.fixture
def bond_no_subs():
    """Returns a Bond with no subscribers"""
    return Bond(bond_id='HostAcctA-SubAcctB',
                host_account_id='HostAcctA',
                sub_account_id='SubAcctB',
                host_cost_center='HostCostCenterA',
                sub_cost_center='SubCostCenterB')


@pytest.fixture
def bond_with_subs():
    """Return a Bond with an existing set of subscribers"""
    subs = {
            'eniesc200': Subscriber(sid='eniesc200',
                                    name='Ed',
                                    email='ed@mail.com'),
            'tfomoo100': Subscriber(sid='tfomoo100',
                                    name='Tom',
                                    email='tom@snail.com'),
            'bfoere300': Subscriber(sid='bfoere300',
                                    name='Bill',
                                    email='bill@mojo.com')
    }
    return Bond(bond_id='HostAcctA-SubAcctB',
                host_account_id='HostAcctA',
                sub_account_id='SubAcctB',
                host_cost_center='HostCostCenterA',
                sub_cost_center='SubCostCenterB',
                subscribers=subs)


@pytest.fixture(scope='function')
def populated_table(table):
    """Pre-loaded DynamoDB table for get tests."""
    subs = {
            'eniesc200': Subscriber(sid='eniesc200',
                                    name='Ed',
                                    email='ed@mail.com'),
            'tfomoo100': Subscriber(sid='tfomoo100',
                                    name='Tom',
                                    email='tom@snail.com'),
            'bfoere300': Subscriber(sid='bfoere300',
                                    name='Bill',
                                    email='bill@mojo.com'),
            'yonou100': Subscriber(sid='yonou100',
                                   name='Yofo',
                                   email='yofu@yosuysg.com'),
            'vdingdo200': Subscriber(sid='vdingdo200',
                                     name='Vince',
                                     email='vinn@mojo.com'),
            'terfo000': Subscriber(sid='terfo000',
                                   name='Bob',
                                   email='bob@mojo.com'),
            'ming007': Subscriber(sid='ming007',
                                  name='Ming',
                                  email='emp@ming.com')
    }
    items = [
        {'bond_id': 'H0001-S0001',
         'host_account_id': 'H0001',
         'sub_account_id': 'S0001',
         'host_cost_center': 'CC001',
         'sub_cost_center': 'CC010',
         'subscribers': {}
         }, {
         'bond_id': 'H0002-S0002',
         'host_account_id': 'H0002',
         'sub_account_id': 'S0002',
         'host_cost_center': 'CC002',
         'sub_cost_center': 'CC010',
         'subscribers': jsonable_encoder(subs)
         }, {
         'bond_id': 'H0002-S0003',
         'host_account_id': 'H0002',
         'sub_account_id': 'S0003',
         'host_cost_center': 'CC002',
         'sub_cost_center': 'CC012',
         'subscribers': jsonable_encoder(subs)
         }, {
         'bond_id': 'H0001-S0002',
         'host_account_id': 'H0001',
         'sub_account_id': 'S0002',
         'host_cost_center': 'CC001',
         'sub_cost_center': 'CC012',
         'subscribers': jsonable_encoder(subs)
         }, {
         'bond_id': 'H0003-S0004',
         'host_account_id': 'H0003',
         'sub_account_id': 'S0004',
         'host_cost_center': 'CC013',
         'sub_cost_center': 'CC010',
         'subscribers': jsonable_encoder(subs)
         }
    ]
    for r in items:
        table.put_item(Item=r)
    yield table


def test_add_bond_no_subs(table, bond_no_subs):
    """Add a bond to DynamoDB without subscribers"""
    bond = crud.create_bond(bond_no_subs)
    response = table.query(
        ProjectionExpression="bond_id, subscribers",
        KeyConditionExpression=Key('bond_id').eq('HostAcctA-SubAcctB')
        )
    # print(response)
    assert bond.subscribers.__len__() == 0
    assert response.get("Count") == 1
    items = response.get("Items")
    assert len(items[0]["subscribers"]) == 0


def test_add_bond(table, bond_with_subs):
    """Add a bond to DynamoDB with subscribers"""
    bond = crud.create_bond(bond_with_subs)
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('HostAcctA-SubAcctB')
        )
    # print(response)
    assert bond.subscribers.__len__() == 3
    assert response.get("Count") == 1
    items = response.get("Items")
    assert items[0]["bond_id"] == 'HostAcctA-SubAcctB'
    assert items[0]["host_account_id"] == 'HostAcctA'
    assert items[0]["sub_account_id"] == 'SubAcctB'
    assert items[0]["host_cost_center"] == 'HostCostCenterA'
    assert items[0]["sub_cost_center"] == 'SubCostCenterB'
    assert len(items[0]["subscribers"]) == 3


def test_add_bond_already_exists(table, bond_no_subs):
    """Add a bond that already exists in DynamoDB. It will raise an error."""
    table.put_item(Item={
                    'bond_id': bond_no_subs.bond_id,
                    'host_account_id': bond_no_subs.host_account_id,
                    'sub_account_id': bond_no_subs.sub_account_id,
                    'host_cost_center': bond_no_subs.host_cost_center,
                    'sub_cost_center': bond_no_subs.sub_cost_center,
                    'subscribers': {}
                    })

    # create a new bond that shares the same partition key as the one
    # we just inserted.
    new_bond = Bond(bond_id=bond_no_subs.bond_id,
                    host_account_id='Foo',
                    sub_account_id='Bar',
                    host_cost_center='Fuz',
                    sub_cost_center='Boo')

    # will throw a KeyError on insert as that partition key already exists
    with pytest.raises(ConditionalCheckError):
        crud.create_bond(new_bond)

    # make sure the original bond is untouched.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('HostAcctA-SubAcctB')
    )
    # print(response)

    # assert the original bond is still there and untouched.
    assert response.get("Count") == 1
    items = response.get("Items")
    assert items[0]["bond_id"] == bond_no_subs.bond_id
    assert items[0]["host_account_id"] == bond_no_subs.host_account_id
    assert items[0]["sub_account_id"] == bond_no_subs.sub_account_id
    assert items[0]["host_cost_center"] == bond_no_subs.host_cost_center
    assert items[0]["sub_cost_center"] == bond_no_subs.sub_cost_center
    assert len(items[0]["subscribers"]) == 0


def test_update_bond(table, bond_with_subs):
    """Update a bond with changed values and adding a new subscriber."""
    table.put_item(Item={
                    'bond_id': bond_with_subs.bond_id,
                    'host_account_id': bond_with_subs.host_account_id,
                    'sub_account_id': bond_with_subs.sub_account_id,
                    'host_cost_center': bond_with_subs.host_cost_center,
                    'sub_cost_center': bond_with_subs.sub_cost_center,
                    'subscribers': jsonable_encoder(bond_with_subs.subscribers)
                    })

    # create the same bond with updated values and with a new subscriber
    upd_bond = Bond(bond_id=bond_with_subs.bond_id,
                    host_account_id=bond_with_subs.host_account_id,
                    sub_account_id=bond_with_subs.sub_account_id,
                    host_cost_center='Fuz',
                    sub_cost_center='Boo',
                    subscribers=bond_with_subs.subscribers)
    upd_bond.add_subscriber(Subscriber(sid='jbojo',
                                       name='Joe Bojo',
                                       email='bogo@mail.com'))

    # update the bond
    bond = crud.update_bond(upd_bond)
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('HostAcctA-SubAcctB')
        )
    # print(response)
    assert bond.subscribers.__len__() == 4
    assert response.get("Count") == 1
    items = response.get("Items")
    assert items[0]["bond_id"] == 'HostAcctA-SubAcctB'
    assert items[0]["host_account_id"] == 'HostAcctA'
    assert items[0]["sub_account_id"] == 'SubAcctB'
    assert items[0]["host_cost_center"] == 'Fuz'
    assert items[0]["sub_cost_center"] == 'Boo'
    assert len(items[0]["subscribers"]) == 4


def test_update_bond_not_exists(table, bond_no_subs):
    """Try to update a bond that does not exist. It will raise an error."""
    # will throw a ConditionalCheckError on update as that partition
    # key does not exists
    with pytest.raises(ConditionalCheckError):
        crud.update_bond(bond_no_subs)

    # make sure the bond has not been inserted.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('HostAcctA-SubAcctB')
    )
    # print(response)
    assert response.get("Count") == 0


def test_delete(table, bond_no_subs):
    """Delete a bond."""
    table.put_item(Item={
                    'bond_id': bond_no_subs.bond_id,
                    'host_account_id': bond_no_subs.host_account_id,
                    'sub_account_id': bond_no_subs.sub_account_id,
                    'host_cost_center': bond_no_subs.host_cost_center,
                    'sub_cost_center': bond_no_subs.sub_cost_center,
                    'subscribers': {}
                    })
    crud.delete_bond(bond_no_subs.bond_id)

    # make sure the bond has gone.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq('HostAcctA-SubAcctB')
    )
    # print(response)
    assert response.get("Count") == 0


def test_delete_not_exists(table, bond_no_subs):
    """Delete a bond that does not exist. It will do nothing."""
    crud.delete_bond(bond_no_subs.bond_id)


def test_add_subscriber_empty_bond(table, bond_no_subs):
    """
    Add a new subscriber to a bond with no current subscribers.
    """
    table.put_item(Item={
                    'bond_id': bond_no_subs.bond_id,
                    'host_account_id': bond_no_subs.host_account_id,
                    'sub_account_id': bond_no_subs.sub_account_id,
                    'host_cost_center': bond_no_subs.host_cost_center,
                    'sub_cost_center': bond_no_subs.sub_cost_center,
                    'subscribers': {}
                    })

    crud.add_subscriber(bond_no_subs.bond_id,
                        Subscriber(sid='jbojo',
                                   name='Joe Bojo',
                                   email='bogo@mail.com'))

    # make sure the subscriber was added.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq(bond_no_subs.bond_id)
    )
    assert response.get("Count") == 1
    items = response.get("Items")
    subs = items[0]["subscribers"]
    assert len(subs) == 1
    assert subs['jbojo']['sid'] == 'jbojo'
    assert subs['jbojo']['name'] == 'Joe Bojo'
    assert subs['jbojo']['email'] == 'bogo@mail.com'


def test_add_subscriber_full_bond(table, bond_with_subs):
    """
    Add a new subscriber to a bond that already has subscribers.
    """
    table.put_item(Item={
        'bond_id': bond_with_subs.bond_id,
        'host_account_id': bond_with_subs.host_account_id,
        'sub_account_id': bond_with_subs.sub_account_id,
        'host_cost_center': bond_with_subs.host_cost_center,
        'sub_cost_center': bond_with_subs.sub_cost_center,
        'subscribers': jsonable_encoder(bond_with_subs.subscribers)
    })

    crud.add_subscriber(bond_with_subs.bond_id,
                        Subscriber(sid='jbojo',
                                   name='Joe Bojo',
                                   email='bogo@mail.com'))

    # make sure the subscriber was added.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq(bond_with_subs.bond_id)
    )
    assert response.get("Count") == 1
    items = response.get("Items")
    subs = items[0]["subscribers"]
    assert len(subs) == 4
    assert subs['jbojo']['sid'] == 'jbojo'
    assert subs['jbojo']['name'] == 'Joe Bojo'
    assert subs['jbojo']['email'] == 'bogo@mail.com'


def test_add_subscriber_exists(table, bond_with_subs):
    """
    Try to add a subscriber that is already listed in the bond. It will
    overwrite what was there, i.e. an update.
    """
    table.put_item(Item={
        'bond_id': bond_with_subs.bond_id,
        'host_account_id': bond_with_subs.host_account_id,
        'sub_account_id': bond_with_subs.sub_account_id,
        'host_cost_center': bond_with_subs.host_cost_center,
        'sub_cost_center': bond_with_subs.sub_cost_center,
        'subscribers': jsonable_encoder(bond_with_subs.subscribers)
    })

    crud.add_subscriber(bond_with_subs.bond_id,
                        Subscriber(sid='tfomoo100',
                                   name='Foo',
                                   email='buzz@mail.com'))

    # make sure the subscriber was added.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq(bond_with_subs.bond_id)
    )
    assert response.get("Count") == 1
    items = response.get("Items")
    subs = items[0]["subscribers"]
    assert len(subs) == 3
    assert subs['tfomoo100']['sid'] == 'tfomoo100'
    assert subs['tfomoo100']['name'] == 'Foo'
    assert subs['tfomoo100']['email'] == 'buzz@mail.com'


def test_add_subscriber_no_bond(populated_table):
    """
    Try to add a subscriber to a non-existent bond.
    It will throw a ConditionalCheckError as that bond does not exist.
    """
    with pytest.raises(ConditionalCheckError):
        crud.add_subscriber("garbage",
                            Subscriber(sid='jbojo',
                                       name='Joe Bojo',
                                       email='bogo@mail.com'))


def test_remove_subscriber_empty_bond(table, bond_no_subs):
    """
    Try to remove a subscriber from a bond with no current subscribers.
    Nothing will happen. The bond will not change.
    """
    table.put_item(Item={
        'bond_id': bond_no_subs.bond_id,
        'host_account_id': bond_no_subs.host_account_id,
        'sub_account_id': bond_no_subs.sub_account_id,
        'host_cost_center': bond_no_subs.host_cost_center,
        'sub_cost_center': bond_no_subs.sub_cost_center,
        'subscribers': {}
    })

    crud.remove_subscriber(bond_no_subs.bond_id, 'jbojo')

    # make sure the bond is untouched.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq(bond_no_subs.bond_id)
    )
    assert response.get("Count") == 1
    items = response.get("Items")
    assert items[0]["bond_id"] == bond_no_subs.bond_id
    assert items[0]["host_account_id"] == bond_no_subs.host_account_id
    assert items[0]["sub_account_id"] == bond_no_subs.sub_account_id
    assert items[0]["host_cost_center"] == bond_no_subs.host_cost_center
    assert items[0]["sub_cost_center"] == bond_no_subs.sub_cost_center
    assert len(items[0]["subscribers"]) == 0


def test_remove_subscriber_full_bond(table, bond_with_subs):
    """
    Remove a subscriber from a bond that contains that subscriber.
    """
    table.put_item(Item={
        'bond_id': bond_with_subs.bond_id,
        'host_account_id': bond_with_subs.host_account_id,
        'sub_account_id': bond_with_subs.sub_account_id,
        'host_cost_center': bond_with_subs.host_cost_center,
        'sub_cost_center': bond_with_subs.sub_cost_center,
        'subscribers': jsonable_encoder(bond_with_subs.subscribers)
    })

    crud.remove_subscriber(bond_with_subs.bond_id, 'bfoere300')

    # make sure the subscriber was removed.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq(bond_with_subs.bond_id)
    )
    assert response.get("Count") == 1
    items = response.get("Items")
    assert items[0]["bond_id"] == bond_with_subs.bond_id
    assert items[0]["host_account_id"] == bond_with_subs.host_account_id
    assert items[0]["sub_account_id"] == bond_with_subs.sub_account_id
    assert items[0]["host_cost_center"] == bond_with_subs.host_cost_center
    assert items[0]["sub_cost_center"] == bond_with_subs.sub_cost_center
    assert len(items[0]["subscribers"]) == 2
    assert 'bfoere300' not in items[0]["subscribers"].keys()


def test_remove_subscriber_full_bond_not_exists(table, bond_with_subs):
    """
    Remove a subscriber from a bond that contains subs, but not that one.
    Nothing will happen. The bond will not change.
    """
    table.put_item(Item={
        'bond_id': bond_with_subs.bond_id,
        'host_account_id': bond_with_subs.host_account_id,
        'sub_account_id': bond_with_subs.sub_account_id,
        'host_cost_center': bond_with_subs.host_cost_center,
        'sub_cost_center': bond_with_subs.sub_cost_center,
        'subscribers': jsonable_encoder(bond_with_subs.subscribers)
    })

    crud.remove_subscriber(bond_with_subs.bond_id, 'garbage')

    # make sure the subscriber was removed.
    response = table.query(
        ProjectionExpression="bond_id, host_account_id, sub_account_id, "
                             "host_cost_center, sub_cost_center, subscribers",
        KeyConditionExpression=Key('bond_id').eq(bond_with_subs.bond_id)
    )
    assert response.get("Count") == 1
    items = response.get("Items")
    assert items[0]["bond_id"] == bond_with_subs.bond_id
    assert items[0]["host_account_id"] == bond_with_subs.host_account_id
    assert items[0]["sub_account_id"] == bond_with_subs.sub_account_id
    assert items[0]["host_cost_center"] == bond_with_subs.host_cost_center
    assert items[0]["sub_cost_center"] == bond_with_subs.sub_cost_center
    assert len(items[0]["subscribers"]) == 3
    assert 'garbage' not in items[0]["subscribers"].keys()


def test_remove_subscriber_no_bond(populated_table):
    """
    Try to remove a subscriber from a non-existent bond.
    It will throw a ConditionalCheckError as that bond does not exist.
    """
    with pytest.raises(ConditionalCheckError):
        crud.remove_subscriber("garbage", 'jbojo')


def test_get_bond(populated_table):
    """Find a bond with the given bond id."""
    bond = crud.get_bond('H0002-S0003')

    assert bond.host_account_id == 'H0002'
    assert bond.sub_account_id == 'S0003'
    assert bond.host_cost_center == 'CC002'
    assert bond.sub_cost_center == 'CC012'
    assert len(bond.subscribers) == 7
    assert bond.subscribers.get('eniesc200').sid == 'eniesc200'
    assert bond.subscribers.get('eniesc200').name == 'Ed'
    assert bond.subscribers.get('eniesc200').email == 'ed@mail.com'
    assert bond.subscribers.get('tfomoo100').name == 'Tom'
    assert bond.subscribers.get('bfoere300').name == 'Bill'
    assert bond.subscribers.get('yonou100').name == 'Yofo'
    assert bond.subscribers.get('vdingdo200').name == 'Vince'
    assert bond.subscribers.get('terfo000').name == 'Bob'
    assert bond.subscribers.get('ming007').name == 'Ming'


def test_get_bond_not_found(populated_table):
    """Get a bond that does not exist. None will be returned."""
    bond = crud.get_bond('rhubarb')
    assert bond is None


def test_get_bond_by_host_cost_center(populated_table):
    """
    Get all bonds for a given host cost center.
    """
    bonds = crud.get_bonds_by_host_cost_center(host_cost_center='CC001')
    assert len(bonds) == 2
    assert 'H0001-S0001' in [bond.bond_id for bond in bonds]
    assert 'H0001-S0002' in [bond.bond_id for bond in bonds]


def test_get_bond_by_host_cost_center_not_found(populated_table):
    """
    Search for a host cost center that does not exist. Returns an empty list.
    """
    bonds = crud.get_bonds_by_host_cost_center(host_cost_center='Blah')
    assert len(bonds) == 0


def test_get_bond_by_host_account_id(populated_table):
    """
    Get all bonds for a given host account id.
    """
    bonds = crud.get_bonds_by_host_account_id(host_account_id="H0002")
    assert len(bonds) == 2
    assert 'H0002-S0002' in [bond.bond_id for bond in bonds]
    assert 'H0002-S0003' in [bond.bond_id for bond in bonds]


def test_get_bond_by_host_account_id_not_found(populated_table):
    """
    Search for a host account id that does not exist. Returns an empty list.
    """
    bonds = crud.get_bonds_by_host_account_id(host_account_id='Blah')
    assert len(bonds) == 0


def test_get_bond_by_sub_cost_center(populated_table):
    """
    Get all bonds for a given subscriber cost center.
    """
    bonds = crud.get_bonds_by_sub_cost_center(sub_cost_center='CC010')
    assert len(bonds) == 3
    assert 'H0001-S0001' in [bond.bond_id for bond in bonds]
    assert 'H0002-S0002' in [bond.bond_id for bond in bonds]
    assert 'H0003-S0004' in [bond.bond_id for bond in bonds]


def test_get_bond_by_sub_cost_center_not_found(populated_table):
    """
    Search for a subscriber cost center that doesn't exist. Returns an empty
    list.
    """
    bonds = crud.get_bonds_by_sub_cost_center(sub_cost_center='Blah')
    assert len(bonds) == 0


def test_get_bond_by_sub_account_id(populated_table):
    """
    Get all bonds for a given subscriber account id.
    """
    bonds = crud.get_bonds_by_sub_account_id(sub_account_id="S0004")
    assert len(bonds) == 1
    assert 'H0003-S0004' in [bond.bond_id for bond in bonds]


def test_get_bond_by_sub_account_id_not_found(populated_table):
    """
    Search for a subscriber account id that doesn't exist. Returns an empty
    list.
    """
    bonds = crud.get_bonds_by_sub_account_id(sub_account_id='Blah')
    assert len(bonds) == 0
