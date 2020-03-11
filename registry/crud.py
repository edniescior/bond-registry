"""
A module for performing CRUD (Create, Retrieve, Update and Delete) operations
on a registry of bonds that are persisted in a database (Dynamodb).

A bond represents a relationship between two parties (accounts) whereby one
party (the subscriber account) promises to pay the other (the host account)
for services provided by the host. This is also known as a 'charge-back
relationship'.

The natural key for a bond is a composite of host account id and subscriber
account id.

A cost center represents a funding entity and is used to group accounts.
There is a one-to-many relationship between cost centers and accounts. Host and
subscriber accounts may belong to the same cost center.

Each bond maintains a list of subscribers. These are individuals who are
affiliated with the subscriber account and are authorized, based on the bond,
to request services from the host account.

Available functions:
- create_bond: Insert a new bond into the database.
- update_bond: Update bond values in the database.
- delete_bond: Delete a bond from the database.
- get_bond: Fetch a bond from the database based on the bond's unique id.
- get_bonds_by_host_cost_center: Fetch all bonds for a host cost center.
- get_bonds_by_host_account_id: Fetch all bonds for a host account.
- get_bonds_by_sub_cost_center: Fetch all bonds for a subscriber cost center.
- get_bonds_by_sub_account_id: Fetch all bonds for a subscriber account.
- add_subscriber: Add a new subscriber to the bond.
- remove_subscriber: Remove a subscriber from a bond.
"""
from registry.models import Bond, Subscriber
from registry import logger
from registry.db import db_connector, ConditionalCheckError, \
    RegistryClientError
from typing import List
from fastapi.encoders import jsonable_encoder

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


@db_connector
def create_bond(conn, bond: Bond) -> Bond:
    """Insert a new bond.

    Args:
        conn (func): A connection to the Dynamodb table (from db_connector).
        bond (Bond): The bond object to insert.

    Raises:
        RegistryClientError if connecting to or querying the database fails.
        ConditionalCheckError if the bond already exists.

    Returns:
        The bond object inserted."""
    logger.debug(f"crud: create bond: bond={bond}")

    try:
        response = conn.put_item(Item={
            'bond_id': bond.bond_id,
            'host_account_id': bond.host_account_id,
            'sub_account_id': bond.sub_account_id,
            'host_cost_center': bond.host_cost_center,
            'sub_cost_center': bond.sub_cost_center,
            'subscribers': jsonable_encoder(bond.subscribers)
        }, ConditionExpression='attribute_not_exists(bond_id)')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.debug(f"crud: bond already exists: bond_id={bond.bond_id}")
            raise ConditionalCheckError(f"Bond already exists: "
                                        f"bond_id={bond.bond_id}")
        else:
            logger.error("crud: Unexpected error: %s" % e)
            raise RegistryClientError(f"Unexpected error querying the "
                                      f"registry: {str(e)}")
    logger.debug(f"Dynamodb response={response}")
    return bond


@db_connector
def update_bond(conn, bond: Bond) -> Bond:
    """Update a bond.

    Args:
        conn (func): A connection to the Dynamodb table (from db_connector).
        bond (Bond): The bond object to update.

    Raises:
        RegistryClientError if connecting to or querying the database fails.
        ConditionalCheckError if the bond does not exist.

    Returns:
        The bond object updated."""
    logger.debug(f"crud: update bond: bond={bond}")

    try:
        response = conn.update_item(
            Key={
                'bond_id': bond.bond_id
            },
            UpdateExpression="set host_account_id = :had, " +
                             "sub_account_id = :sad, " +
                             "host_cost_center = :hcc, " +
                             "sub_cost_center = :scc, " +
                             "subscribers = :sub",
            ExpressionAttributeValues={
                ':had': bond.host_account_id,
                ':sad': bond.sub_account_id,
                ':hcc': bond.host_cost_center,
                ':scc': bond.sub_cost_center,
                ':sub': jsonable_encoder(bond.subscribers)
            },
            ConditionExpression='attribute_exists(bond_id)',
            ReturnValues="UPDATED_NEW")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.debug(f"crud: bond not found: bond_id={bond.bond_id}")
            raise ConditionalCheckError(f"Bond not found: "
                                        f"bond_id={bond.bond_id}")
        else:
            logger.error("crud: Unexpected error: %s" % e)
            raise RegistryClientError(f"Unexpected error querying the "
                                      f"registry: {str(e)}")
    logger.debug(f"Dynamodb response={response}")
    return bond


@db_connector
def delete_bond(conn, bond_id: str) -> None:
    """Delete a bond. Does nothing if the bond does not exist.

    Args:
        conn (func): A connection to the Dynamodb table (from db_connector).
        bond_id (str): The bond id of the bond to delete.

    Raises:
        RegistryClientError if connecting to or querying the database fails."""
    logger.debug(f"crud: delete bond: bond_id={bond_id}")

    try:
        response = conn.delete_item(
            Key={
                'bond_id': bond_id
            })
    except ClientError as e:
        logger.error("crud: Unexpected error: %s" % e)
        raise RegistryClientError(f"Unexpected error querying the "
                                  f"registry: {str(e)}")
    logger.debug(f"Dynamodb response={response}")


def bond_from_item(item) -> Bond:
    """A helper function to convert a DynamoDB item to a Bond object."""
    bond = Bond(
        bond_id=item["bond_id"],
        host_account_id=item["host_account_id"],
        sub_account_id=item["sub_account_id"],
        host_cost_center=item["host_cost_center"],
        sub_cost_center=item["sub_cost_center"],
        subscribers=item["subscribers"]
    )
    return bond


@db_connector
def execute_query(conn, query_expr: dict) -> str:
    """A helper function to execute a query against Dynamo db.

    Args:
        conn (func): A connection to the Dynamodb table (from db_connector).
        query_expr (dict): A dictionary containing Dynamodb-specific query
            attributes: KeyConditionExpression and IndexName (if applicable).

    Raises:
        RegistryClientError if connecting to or querying the database fails.

    Returns:
        The Dynamodb query API results as JSON."""
    try:
        if 'IndexName' not in query_expr.keys():
            response = conn.query(
                KeyConditionExpression=query_expr['KeyConditionExpression']
            )
        else:
            response = conn.query(
                IndexName=query_expr['IndexName'],
                KeyConditionExpression=query_expr['KeyConditionExpression']
            )
    except ClientError as e:
        logger.error("crud: Unexpected error: %s" % e)
        raise RegistryClientError(f"Unexpected error querying the "
                                  f"registry: {str(e)}")
    logger.debug(f"Dynamodb response={response}")
    return response


def get_bond(bond_id: str) -> Bond:
    """Get a bond with the given id.

    Args:
        bond_id (str): The bond id of the bond to fetch.

    Raises:
        RegistryClientError if connecting to or querying the database fails.

    Returns:
        The requested bond object or None if not found."""
    logger.debug(f"crud: get bond: bond_id={bond_id}")

    query_expr = {'KeyConditionExpression': Key('bond_id').eq(bond_id)}
    response = execute_query(query_expr)

    if len(response["Items"]) == 0:
        logger.debug(f"crud: bond not found: bond_id={bond_id}")
        return None

    return bond_from_item(response["Items"][0])


def get_bonds_by_host_cost_center(host_cost_center: str) -> List[Bond]:
    """Get all bonds for the given *host* cost center.

    Args:
        host_cost_center (str): The host cost center identifier to search on.

    Raises:
        RegistryClientError if connecting to or querying the database fails.

    Returns:
        A list of bond objects or an empty list if none are found."""
    logger.debug(f"crud: get bonds by host cost center: "
                 f"host_cost_center={host_cost_center}")
    bonds = []

    query_expr = {
        'IndexName': "bond-host_cost_center-index",
        'KeyConditionExpression': Key('host_cost_center').eq(host_cost_center)
    }
    response = execute_query(query_expr)

    for item in response['Items']:
        bonds.append(bond_from_item(item))
    return bonds


def get_bonds_by_host_account_id(host_account_id: str) -> List[Bond]:
    """Get all bonds for the given *host* account.

    Args:
        host_account_id (str): The host account identifier to search on.

    Raises:
        RegistryClientError if connecting to or querying the database fails.

    Returns:
        A list of bond objects or an empty list if none are found."""
    logger.debug(f"crud: get bonds by host account id: "
                 f"host_account_id={host_account_id}")
    bonds = []

    query_expr = {
        'IndexName': "bond-host_account_id-index",
        'KeyConditionExpression': Key('host_account_id').eq(host_account_id)
    }
    response = execute_query(query_expr)

    for item in response['Items']:
        bonds.append(bond_from_item(item))
    return bonds


def get_bonds_by_sub_cost_center(sub_cost_center: str) -> List[Bond]:
    """Get all bonds for the given *subscriber* cost center.

    Args:
        sub_cost_center (str): The subscriber cost center id to search on.

    Raises:
        RegistryClientError if connecting to or querying the database fails.

    Returns:
        A list of bond objects or an empty list if none are found."""
    logger.debug(f"crud: get bonds by sub cost center: "
                 f"sub_cost_center={sub_cost_center}")
    bonds = []

    query_expr = {
        'IndexName': "bond-sub_cost_center-index",
        'KeyConditionExpression': Key('sub_cost_center').eq(sub_cost_center)
    }
    response = execute_query(query_expr)

    for item in response['Items']:
        bonds.append(bond_from_item(item))
    return bonds


def get_bonds_by_sub_account_id(sub_account_id: str) -> List[Bond]:
    """Get all bonds for the given *subscriber* account.

    Args:
        sub_account_id (str): The subscriber account identifier to search on.

    Raises:
        RegistryClientError if connecting to or querying the database fails.

    Returns:
        A list of bond objects or an empty list if none are found."""
    logger.debug(f"crud: get bonds by sub account id: "
                 f"sub_account_id={sub_account_id}")
    bonds = []

    query_expr = {
        'IndexName': "bond-sub_account_id-index",
        'KeyConditionExpression': Key('sub_account_id').eq(sub_account_id)
    }
    response = execute_query(query_expr)

    for item in response['Items']:
        bonds.append(bond_from_item(item))
    return bonds


def add_subscriber(bond_id: str, sub: Subscriber) -> Bond:
    """Add a subscriber to a bond. Overwrite if the subscriber is already
    present.

    Args:
        bond_id (str): The bond id of the bond to add the subscriber to.
        sub (Subscriber): The subscriber object to add to the bond.

    Raises:
        RegistryClientError if connecting to or querying the database fails.
        ConditionalCheckError if the bond does not exist.

    Returns:
        The updated bond object."""
    logger.debug(f"crud: add subscriber: bond_id={bond_id}, sub={sub}")
    bond = get_bond(bond_id)
    if bond is None:
        raise ConditionalCheckError(f'Bond {bond_id} not found. '
                                    f'Cannot add subscriber {sub.sid}.')
    bond.add_subscriber(sub)
    return update_bond(bond)


def remove_subscriber(bond_id: str, sid: str) -> Bond:
    """Remove a subscriber from a bond. Ignore if the subscriber is not
    a current subscriber attached to the bond.

    Args:
        bond_id (str): The bond id of the bond to remove the subscriber from.
        sid (str): The subscriber identifier of the subscriber to be removed.

    Raises:
        RegistryClientError if connecting to or querying the database fails.
        ConditionalCheckError if the bond does not exist.

    Returns:
        The updated bond object."""
    logger.debug(f"crud: remove subscriber: bond_id={bond_id}, sid={sid}")
    bond = get_bond(bond_id)
    if bond is None:
        raise ConditionalCheckError(f'Bond {bond_id} not found. '
                                    f'Cannot remove subscriber {sid}.')
    bond.remove_subscriber(sid)
    return update_bond(bond)
