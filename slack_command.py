import boto3
import json
import logging
import os

from base64 import b64decode
from urllib.parse import parse_qs

ADDRESS = os.environ['ADDRESS']
DATA_TABLE = os.environ['DATA_TABLE']
TOKEN_PARAMETER = os.environ['TOKEN_PARAMETER']

ssm = boto3.client('ssm')
expected_token = ssm.get_parameter(Name=TOKEN_PARAMETER, WithDecryption=True)['Parameter']['Value']

dynamodb = boto3.resource('dynamodb')
trucks_table = dynamodb.Table(DATA_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_data():
    response = trucks_table.get_item(
        Key={
            'id': ADDRESS,
        }
    )
    item = response['Item']
    return item['data']

def format_data(data):
    lines = []

    for item in data:
        location = item['location']
        lines.append("%s (%s)" % (location['name'], location['address']))

        for truck in item['trucks']:
            lines.append("%s (%s)" % (truck['name'], truck['description']))

    return '\n'.join(lines)

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': str(err) if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def lambda_handler(event, context):
    params = parse_qs(event['body'])

    if 'token' in params:
        token = params['token'][0]
        if token != expected_token:
            logger.error("Request token (%s) does not match expected", token)
            return respond(Exception('Invalid request token'))
    elif 'trigger' not in event or event['trigger'] != 'canary':
        logger.error('No request token provided')
        return respond(Exception('Invalid request token'))

    data = get_data()
    formatted_data = format_data(data)

    result = {
        'response_type': 'in_channel',
        'text': formatted_data
    }

    return respond(None, result)
