import boto3
import json
import logging
import os

from base64 import b64decode
from urllib.parse import parse_qs

ADDRESS = os.environ['address']
DATA_TABLE = os.environ['data_table']
TOKEN_PARAMETER = os.environ['token_parameter']

ssm = boto3.client('ssm')
expected_token = ssm.get_parameter(Name=TOKEN_PARAMETER, WithDecryption=True)['Parameter']['Value']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
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
    elif event['trigger'] != 'canary':
        logger.error('No request token provided')
        return respond(Exception('Invalid request token'))

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]

    return respond(None, "%s invoked %s in %s" % (user, command, channel))
