"""
A decorator function to manage connectivity to the bond table in Dynamodb.
"""
from registry import logger

import boto3
from botocore.exceptions import ClientError


class RegistryClientError(Exception):
    """Raised if we fail to connect to the registry database."""
    pass


class ConditionalCheckError(Exception):
    """
    Raised if we get an error back from the registry database when we query it.
    """
    pass


def db_connector(func):
    def with_connection_(*args, **kwargs):
        try:
            logger.debug(f'DynamoDB: ONLINE mode. Connecting to cloud db.')
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table("bond")
            logger.debug(f'DynamoDB: Connected to {table.table_arn}')
            rv = func(table, *args, **kwargs)
        except ClientError as err:
            logger.exception("DynamoDB: Failed to connect to the bond "
                             "table: %s" % err)
            raise RegistryClientError(f"Failed to connect to the database: "
                                      f"{str(err)}")
        return rv
    return with_connection_
