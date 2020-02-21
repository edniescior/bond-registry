"""
A decorator function to manage connectivity to the bond table in Dynamodb.
"""
from registry import logger
import os
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

        """
        Open a connection to DynamoDB.
        If IS_OFFLINE is set, then connect to the local instance of DynamoDB
        running in Docker; Otherwise, connect to the cloud service.
        (Note: moto mock DynamoDB uses this path, i.e. IS_OFFLINE is false.)
        """
        is_offline = os.environ.get("IS_OFFLINE")

        try:
            if is_offline:
                logger.debug(f'DynamoDB: OFFLINE mode. Connecting to local db')
                dynamodb = \
                    boto3.resource(
                        "dynamodb",
                        endpoint_url='http://dynamodb-local:8000/',
                        region_name='us-west-2',
                        aws_access_key_id='AWS_ACCESS_KEY_ID',
                        aws_secret_access_key='AWS_SECRET_ACCESS_KEY')
            else:
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
