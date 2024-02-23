# get data from es
from requests_aws4auth import AWS4Auth
import boto3
import requests
import json

service = 'es'
region = 'us-east-1'
es_url = 'https://search-restaurants-pmwgtzh44lg73zwmzmzvfniz3m.us-east-1.es.amazonaws.com/restaurants/_search'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)


def get_data_from_es(cuisine):
    # using cuisine to search the es, and get all the data
    query = {
        "query": {
            "match": {
                "cuisine": cuisine
            }
        }
    }
    # send req to
    headers = { "Content-Type": "application/json" }
    response = requests.get(es_url, auth=awsauth, headers=headers, data=json.dumps(query))

    if response.status_code == 200:
        results = response.json()
        ids = [hit['_source']['id'] for hit in results['hits']['hits']]
        return ids
    else:
        print(f"ES Error: {response.status_code}")
        return []