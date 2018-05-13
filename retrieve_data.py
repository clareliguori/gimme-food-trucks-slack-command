import boto3
import json
import logging
import os
from time import sleep
from datetime import *
from dateutil.relativedelta import *
from seattle_food_truck import *
from functools import partial
from retrying import retry

ADDRESS = os.environ['ADDRESS']
DATA_TABLE = os.environ['DATA_TABLE']

dynamodb = boto3.resource('dynamodb')
trucks_table = dynamodb.Table(DATA_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_delay=30000)
def get_address_lat_long():
    return lat_long_from_address("%s, Seattle, WA" % (ADDRESS))

def closest_trucks(n, date):
    food_truck_client = SeattleFoodTruckClient()

    lat_long = get_address_lat_long()

    distance_from_reference = partial(haversine_distance, lat_long2=lat_long)

    sorted_locations = sorted(food_truck_client.locations, key=lambda loc: haversine_distance(loc.lat_long, lat_long))

    sorted_close_locations = list(filter(lambda loc: haversine_distance(loc.lat_long, lat_long) < 0.5, sorted_locations))

    truck_count = 0
    trucks = {}

    for location in sorted_close_locations:
        food_truck_client.location = location
        location_trucks = food_truck_client.trucks_on_day(date)
        if location_trucks:
            trucks[location] = location_trucks
            truck_count += len(location_trucks)

        if truck_count >= n:
            break
        else:
            sleep(1) # self-throttle

    return trucks

def store_trucks(trucks_d):
    location_items = []

    for location, trucks in trucks_d.items():
        truck_items = []
        for truck in trucks:
            truck_items.append({
                'name': truck.name,
                'description': truck.food_description
            })

        location_item = {
            'name': location.name,
            'address': location.address
        }

        location_items.append({
            'location': location_item,
            'trucks': truck_items
        })

    trucks_table.put_item(Item={
        'id': ADDRESS,
        'data': location_items
    })

def lambda_handler(event, context):

    truck_date = date.today()
    if truck_date.weekday() > 5:
        truck_date = truck_date + relativedelta(weekday=MO)

    trucks = closest_trucks(10, truck_date)

    store_trucks(trucks)

    return {
        'success' : True
    }
