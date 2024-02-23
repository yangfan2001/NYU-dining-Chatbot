import json
from dynamodb import get_data_from_db
from es import get_data_from_es
import boto3
from botocore.exceptions import ClientError


def receive_message_from_sqs():
    sqs = boto3.client('sqs')
    queue_name = 'chatbot-sqs'
    queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'All'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=10
    )

    if 'Messages' in response:
        message = response['Messages'][0]
        message_body = message['Body']
        dining_info = json.loads(message_body)
        # cuisine = dining_info.get('cuisine')
        # email = dining_info.get('email')
        # location = dining_info.get('location')
        # num_people = dining_info.get('num_people')
        # date = dining_info.get('date')
        # time = dining_info.get('time')
        print(dining_info)

        receipt_handle = message['ReceiptHandle']
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        return dining_info
    else:
        return None

def send_email(subject, body, recipient):
    client = boto3.client('ses', region_name='us-east-1')  #
    try:
        response = client.send_email(
            Source=recipient,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        return response
    except ClientError as error:
        raise Exception(f"Email sending failed: {error.response['Error']['Message']}")


def lambda_handler(event, context):
    try:
        dining_info = receive_message_from_sqs()
        if dining_info is not None:
            cuisine = dining_info.get('cuisine')
            email = dining_info.get('email')
            location = dining_info.get('location')
            num_people = dining_info.get('num_people')
            date = dining_info.get('date')
            time = dining_info.get('time')
            body_head = "Hello! Here are my " + cuisine + " restaurant suggestions for " + str(num_people) + " people, "
            body_head += "for " + date + " at " + time + "\n"
            id_list = get_data_from_es(cuisine)
            restaurant_list = get_data_from_db(id_list)

            content = ""
            # TODO implement
            cnt = 1
            for restaurant in restaurant_list[-3:]:
                restaurant_name = restaurant['name']
                restaurant_address = restaurant['location']['display_address'][0]
                content += str(cnt) + ". " + restaurant_name + ", located at " + restaurant_address + '\n'
                cnt += 1

            greeting = "\n" + "Enjoy Your Meal!\n"

            subject = "Your Restaurant Recommendations"
            body = body_head + content + greeting
            print(body)
            send_email(subject, body, email)
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Email sent successfully'})
            }
    except Exception as e:
        return {
                    'statusCode': 500,
                    'body': json.dumps({'error': str(e)})
        }