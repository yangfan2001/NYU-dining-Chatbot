# fetch data from yelp api
import datetime
from decimal import Decimal
import requests
import boto3

API_KEY = 'lpNM8iKYfz_J6DjN_jngSSR3JP8NhP5tyu59dHFGliGR33a1HbxB2AKuQlHWAUvg7AeboINriqcaxnKRfyxmAvNyJSHgm-LRWHXepgNncnuOMB0ydSxKnejdKmjRZXYx'
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization': 'Bearer %s' % API_KEY}


# using boto3 to access AWS
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('yelp-restaurants')



def convert_floats_to_decimals(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = convert_floats_to_decimals(v)
    elif isinstance(obj, list):
        obj = [convert_floats_to_decimals(v) for v in obj]
    return obj


cnt = 0
def fetch_restaurants(cuisine, location='Manhattan', total=1000):
    global cnt
    restaurants = []
    unique_ids = set()
    for offset in range(0, total, 50):
        params = {
            'term': cuisine + ' restaurants',
            'location': location,
            'limit': 50,
            'offset': offset
        }
        response = requests.get(ENDPOINT, headers=HEADERS, params=params).json()
        for business in response.get('businesses', []):
            if business['id'] not in unique_ids:
                unique_ids.add(business['id'])
                business_id = business['id']
                business['businessId'] = business_id
                business['insertedAtTimestamp'] = datetime.datetime.utcnow().isoformat()
                business['cuisine'] = cuisine
                business = convert_floats_to_decimals(business)
                print("append:",cnt)
                cnt+=1
                response = table.put_item(Item=business)
                print("Item inserted successfully:", response)

        if len(restaurants) >= total:
            break
    return restaurants

# Example usage
cuisines = ['Chinese', 'Italian', 'Mexican', 'Japanese', 'Indian','French']
all_restaurants = []

for cuisine in cuisines:
    all_restaurants += fetch_restaurants(cuisine, total=1000)

print(f"Fetched {len(all_restaurants)} restaurants")
