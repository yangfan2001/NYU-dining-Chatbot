import requests
from requests_aws4auth import AWS4Auth
import boto3
import time

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('yelp-restaurants')


region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

url = 'https://search-restaurants-pmwgtzh44lg73zwmzmzvfniz3m.us-east-1.es.amazonaws.com'

def  scan_dynamodb_table(table, scan_kwargs={}, max_attempts=5):
    attempts = 0
    items = []
    start_key = None

    while attempts < max_attempts:
        try:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            if not start_key:
                break
        except Exception as e:
            attempts += 1
            wait_time = 2 ** attempts
            print(f"waiting..... {wait_time}...")
            time.sleep(wait_time)
            break

    return items

dynamodb_items = scan_dynamodb_table(table)


for item in dynamodb_items:
    document_id = item.get('businessId')
    cuisine = item.get('cuisine')
    document = {
        'id': document_id,
        'cuisine': cuisine
    }
    es_response = requests.put(f"{url}/restaurants/_doc/{document_id}",  # 确保使用正确的索引名和文档ID
                               auth=awsauth,
                               json=document,  # 直接将构造的文档作为 JSON 数据发送
                               headers={"Content-Type": "application/json"})
    print(es_response.text)