import boto3
import datetime
import dateutil.parser
import json
import logging
import math
import os
import time
import re
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def greeting_intent(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'Hi there, how can I help?'}
        }
    }


def thank_you_intent(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'You are welcome!'}
        }
    }


def validate_dining_suggestion(location, cuisine, num_of_people, date, time, email):
    # location only supports Manhattan for now, so no need to validate
    cuisines = ['chinese', 'italian', 'mexican', 'japanese', 'indian', 'french']
    if cuisine is not None and cuisine.lower() not in cuisines:
        print("cuisine:" + cuisine)
        return build_validation_result(
            False,
            'Cuisine',
            'This cuisine is not available. Could you try a different one?')

    if num_of_people is not None:
        num_of_people = int(num_of_people)
        if num_of_people > 30 or num_of_people <= 0:
            return build_validation_result(
                False,
                'NumberOfPeople',
                'We can not deal with this number of people. Please try again.')

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(
                False,
                'Date',
                'I did not understand that, what date would you like to choose?')

        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(
                False,
                'Date',
                'Please provide a date in the future.')

    if time is not None:
        if len(time) != 5:
            return build_validation_result(False, 'Time', 'Please provide a time in the future.')

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            return build_validation_result(False, 'Time', 'Not a valid time')
        if hour < 8 or hour > 23:
            return build_validation_result(False, 'Time', 'We are only open from 8am to 11pm')
        if minute < 0 or minute > 59:
            return build_validation_result(False, 'Time', 'Not a valid time')

    if email is not None:
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(pattern, email):
            return build_validation_result(False, 'Email', 'Not a valid email address')

    return build_validation_result(True, None, None)


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def dining_suggestion_intent(intent_request):
    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    num_people = get_slots(intent_request)["NumberOfPeople"]
    date = get_slots(intent_request)["Date"]
    time = get_slots(intent_request)["Time"]
    email = get_slots(intent_request)["Email"]

    logger.debug(
        'location={}, cuisine={}, num_people={}, date={}, time={}, email={}'.format(location, cuisine, num_people, date,
                                                                                    time, email))

    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(location, cuisine, num_people, date, time, email)

        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                intent_request['sessionAttributes'],
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message'])

        if intent_request['sessionAttributes'] is not None:
            output_session_attributes = intent_request['sessionAttributes']
        else:
            output_session_attributes = {}

        return delegate(output_session_attributes, get_slots(intent_request))

    # Fulfillment
    sqs_client = boto3.client('sqs')
    queue_name = 'chatbot-sqs'

    queue_url_response = sqs_client.get_queue_url(QueueName=queue_name)
    queue_url = queue_url_response['QueueUrl']

    message_body = {"cuisine": cuisine,
           "email": email,
           "location": location,
           "num_people": num_people,
           "date": date,
           "time": time}
    message_body_json = json.dumps(message_body)
    response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body_json)
    logger.debug(response)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {
                     'contentType': 'PlainText',
                     'content': 'You will receive suggestion shortly. Enjoy your meal!'})

def dispatch(intent_request):
    # logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']
    # if intent_name == 'Greeting':
    #     return greeting_intent(intent_request)
    # elif intent_name == 'DiningSuggestions':
    #     return dining_suggestion_intent(intent_request)
    # elif intent_name == 'ThankYou':
    #     return thank_you_intent(intent_request)

    if intent_name == 'DiningSuggestions':
        return dining_suggestion_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
