#
# Generate randomized test data for the bond table in dynamodb.
#
# Note: DynamoDB batch write is limited to 25 items.
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
parser.add_argument('-o',
                    metavar='out_file',
                    type=str,
                    help='Path to output file.')
args = parser.parse_args()
num_records = args.Records

# fake data generator setup
fake = Faker()
fake.add_provider(profile)
fake.add_provider(bank)
fake.add_provider(color)


def gen_item(faker: Faker):
    def gen_random_subs():
        """
        Generate a random number of subscribers (0 to 7) and
        return as a map.
        """
        def gen_sub() -> dict:
            p = faker.profile()
            return {
                "M": {
                    "name": {"S": p['name']},
                    "email": {"S": p['mail']},
                    "sid": {"S": p['username']}
                }
            }

        subscribers = {'M': {}}
        for i in range(0, random.randint(0, 7)):
            sub = gen_sub()
            subscribers['M'][sub['M']['sid']['S']] = sub
        return subscribers

    return {
            "PutRequest": {
                "Item": {
                    "bond_id": {"S": fake.md5()},
                    "host_account_id": {"S": fake.bban()},
                    "sub_account_id": {"S": fake.bban()},
                    "host_cost_center": {"S": fake.safe_color_name()},
                    "sub_cost_center": {"S": fake.safe_color_name()},
                    "subscribers": gen_random_subs()
                }
            }
    }


data = {"bond": []}
for item in (gen_item(fake) for i in range(num_records)):
    data['bond'].append(item)


# pretty print to STDOUT if no output file was provided.
if not args.o:
    print(json.dumps(data, sort_keys=True, indent=4))
else:
    with open(args.o, "w") as write_file:
        json.dump(data, write_file)