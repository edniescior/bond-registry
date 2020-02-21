#
# Generate randomized test data for the bond table in dynamodb.
#
# DynamoDB batch write is limited to 25 items, so we cap it there for now.
#
import argparse
import json
import random

from faker import Faker
from faker.providers import profile, bank, color

parser = argparse.ArgumentParser(description='Generate randomized test data \
                                            for the bond table in dynamodb')
parser.add_argument('Records',
                    metavar='num_records',
                    type=int,
                    help='the number of records to generate (max = 25)')
args = parser.parse_args()
num_records = args.Records if args.Records <= 25 else 25  # cap at 25 records

# fake data generator setup
fake = Faker()
fake.add_provider(profile)
fake.add_provider(bank)
fake.add_provider(color)

records = []
for rec in range(num_records):

    subList = {}
    for i in range(0, random.randint(0, 7)):
        p = fake.profile()
        sub = {
            "M": {
                "name": {"S": p["name"]},
                "email": {"S": p["mail"]},
                "sid": {"S": p["username"]}
            }
        }
        subList[p["username"]] = sub

    record = {
        "PutRequest": {
            "Item": {
                "bond_id": {"S": "TEST007" if rec == 0 else fake.md5()},
                "host_account_id": {"S": fake.bban()},
                "sub_account_id": {"S": fake.bban()},
                "host_cost_center": {"S": fake.safe_color_name()},
                "sub_cost_center": {"S": fake.safe_color_name()},
                "subscribers": {
                    "M": subList
                }
            }
        }
    }
    records.append(record)

data = {"bond": records}

with open("02-load-data.json", "w") as write_file:
    json.dump(data, write_file)
