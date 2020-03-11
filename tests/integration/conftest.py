import pytest
import testcontainers.compose
import requests
import backoff
import boto3
from botocore.exceptions import ClientError
import json
from fastapi.encoders import jsonable_encoder
from registry.models import Subscriber

COMPOSE_PATH = "./"


@pytest.fixture(scope="module")
def compose(request):
    """
    Test fixture to launch the docker containers as per the docker compose
    file. It has a retry loop to ensure the containers are up before
    releasing the tests.
    """

    def fin():
        """
        Tear down handler to bring down the containers once the tests have
        run to completion.
        """
        print("Stopping containers")
        compose.stop()
    request.addfinalizer(fin)

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_time=30)
    def is_up(app_host: str, app_port: str):
        """
        Continually polls the containers with back-off until we get a
        response back and we know the containers are up and running.
        The bond registry container depends on the dynamodb container
        (as per the docker-compose file) so we know that both containers
        are running if api returns a result.
        """
        r = requests.get(f"http://{app_host}:{app_port}/docs")
        assert r.status_code == 200

    print("Starting containers")
    compose = testcontainers.compose.DockerCompose(COMPOSE_PATH)
    compose.start()

    host = compose.get_service_host("bond-registry", 8080)
    port = compose.get_service_port("bond-registry", 8080)
    is_up(host, port)
    return compose


@pytest.fixture(scope="module")
def api_url(compose):
    """
    Provide the URL to the API once the containers are up.
    """
    host = compose.get_service_host("bond-registry", 8080)
    port = compose.get_service_port("bond-registry", 8080)
    return f"{host}:{port}"


@pytest.fixture(scope="module")
def db_url(compose):
    """
    Provide the URL to dynamodb once the containers are up.
    """
    host = compose.get_service_host("dynamodb-local", 8000)
    port = compose.get_service_port("dynamodb-local", 8000)
    return f"{host}:{port}"


@pytest.fixture(scope='module')
def dynamodb(db_url):
    """
    Connect to the local dynamodb container.
    """
    try:
        resource = \
            boto3.resource("dynamodb",
                           endpoint_url=f'http://{db_url}/',
                           region_name='us-west-2',
                           aws_access_key_id='AWS_ACCESS_KEY_ID',
                           aws_secret_access_key='AWS_SECRET_ACCESS_KEY')
    except ClientError as err:
        print(err)
        raise err
    return resource


@pytest.fixture(scope='module')
def table(dynamodb):
    """Create the mock bond table."""
    with open("./localdb/01-create-table.json") as read_file:
        table_def = json.load(read_file)
    try:
        table = dynamodb.create_table(
            TableName=table_def['TableName'],
            BillingMode=table_def['BillingMode'],
            KeySchema=table_def['KeySchema'],
            AttributeDefinitions=table_def['AttributeDefinitions'],
            GlobalSecondaryIndexes=table_def['GlobalSecondaryIndexes'])

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
                                    email='bill@mojo.com')
        }
        items = [
            {'bond_id': '6cc333cd',
             'host_account_id': 'KYOT95889719595091',
             'sub_account_id': 'NSSV61341208978885',
             'host_cost_center': 'yellow',
             'sub_cost_center': 'silver',
             'subscribers': {}
             }, {
                'bond_id': 'bf66a510',
                'host_account_id': 'HAEP29388232018739',
                'sub_account_id': 'WZNH57184416064999',
                'host_cost_center': 'yellow',
                'sub_cost_center': 'white',
                'subscribers': jsonable_encoder(subs)
            }, {
                'bond_id': '3f4436a3',
                'host_account_id': 'BULG01950964065116',
                'sub_account_id': 'PFUP24464317335973',
                'host_cost_center': 'maroon',
                'sub_cost_center': 'navy',
                'subscribers': jsonable_encoder(subs)
            }, {
                'bond_id': '070840c5',
                'host_account_id': 'LXJC36779030364939',
                'sub_account_id': 'OYHE81882804630311',
                'host_cost_center': 'maroon',
                'sub_cost_center': 'olive',
                'subscribers': jsonable_encoder(subs)
            }, {
                'bond_id': 'e6d9c05f',
                'host_account_id': 'YHRH31548177246824',
                'sub_account_id': 'QZUL57771567168857',
                'host_cost_center': 'navy',
                'sub_cost_center': 'aqua',
                'subscribers': jsonable_encoder(subs)
            }, {
                'bond_id': 'deleteme',
                'host_account_id': 'YHRH31548175555555',
                'sub_account_id': 'QZUL57771567777777',
                'host_cost_center': 'navy',
                'sub_cost_center': 'aqua',
                'subscribers': {}
            }, {
                'bond_id': 'eb5e729a',
                'host_account_id': 'YHRH31548177246824',
                'sub_account_id': 'EVJS54814803488145',
                'host_cost_center': 'navy',
                'sub_cost_center': 'orange',
                'subscribers': {}
            }, {
                'bond_id': '2e545043',
                'host_account_id': 'NAMD04758644119335',
                'sub_account_id': 'BVOD03985622038101',
                'host_cost_center': 'green',
                'sub_cost_center': 'orange',
                'subscribers': {}
            }, {
                'bond_id': '402206d5',
                'host_account_id': 'ZGDX86819087481638',
                'sub_account_id': 'CNUE67550266655258',
                'host_cost_center': 'black',
                'sub_cost_center': 'orange',
                'subscribers': {}
            }
        ]
        for r in items:
            table.put_item(Item=r)
    except ClientError as err:
        print(err)
        raise err
    yield table
