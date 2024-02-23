# get data from dynamoDB
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('yelp-restaurants')

def get_data_from_db(id_list):
    # using id to get the data from dynamoDB
    items = []
    for id in id_list:
        response = table.get_item(Key={'businessId': id})
        if 'Item' in response:
            items.append(response['Item'])
    # return all the matched columns:
    return items

