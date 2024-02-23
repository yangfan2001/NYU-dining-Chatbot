import json
import boto3
import os

def lambda_handler(event, context):
    print(event)
    lex_client = boto3.client('lex-runtime')
    messages = event.get('messages')
    
    lambda_response = {
        'statusCode': 400,
        'userid':'test-user',
         'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body':{
            'messages': [
            {
                'type':'unstructured',
                'unstructured':{
                    'text':'No message received'
                }
            }
        ]
        }
    }
    
    if messages:
        botAlias=os.environ['BotAlias']
        botName=os.environ['BotName']
        
        response = lex_client.post_text(
            botName=botName,
            botAlias=botAlias,
            userId='test-user',
            inputText=messages[0]['unstructured']['text']
        )
       
        print(response)
        # Define the response body
         
        lambda_response = {
            'statusCode': 200,
            'userid':'test-user',
             'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body':{
                "messages": [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "text": response['message']
                    }
                }
            ]
            }
        }
    
    # Return the statusCode and the body as a JSON string
    return lambda_response
