import logging
import json
import os
import requests
from laceworksdk import LaceworkClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('Retrieved new message!')
    logger.info("Event: " + str(event))
    logger.info("Context: " + str(context))

    logger.debug('Load body')
    #data=event.get('body')
    data=event
    alertID = event.get('event_id')
    logger.info("Body: " + str(data))
    if data == "" or data is None:
        #Set the data to a default value
        data={}

    logger.debug('Load filter')
    filter=load_parameter(event, 'filter')
    if filter == "" or filter is None:
        #Set filter default behavior to always forward if it's not already set
        logger.info("Filter not configured") 
        filter={"operator": "true"}
    else:
        logger.info("Filter: " + str(filter)) 


    # Instantiate a LaceworkClient instance
    try:
        lacework_client = LaceworkClient(account=os.environ['LwAccount'],
                    api_key=os.environ['LwApiKey'],
                    api_secret=os.environ['LwApiSecret'])
    except Exception as e:
        logger.error(f'Unable to configure Lacework client: {e}')
        
    #Collect Alert Details
    try: 
        #logger.error(event["event_id"])
        #print(data["event_id"])
        alertDetails = lacework_client.alerts.get_details(alertID, "Details")
        #merge alertDetails with data
        data=alertDetails
    except Exception as e:
        logger.error(f'Alert Details search failed: {e}')
    
    logger.debug('Load Webhook URL')
    webhookUrl=load_parameter(event, 'webhookurl')
    logger.debug(webhookUrl) 

    logger.debug('Load Webhook Username')
    webhookUsername=load_parameter(event, 'webhookusername')

    logger.debug('Load Webhook Password')
    webhookPassword=load_parameter(event, 'webhookpassword')

    '''
    logger.debug('Load http method used')
    httpMethod= event['requestContext']['http']['method']
    logger.debug(httpMethod)
    '''
    
    logger.debug('Parse filter')
    filter=parse_json(filter)
    logger.debug('Parse body')
    data=parse_json(data)
    #logger.info(f"Length: {len(data['data'])}")

    logger.debug('Evaluate filter')
    result=eval_filter(filter, data)
    
    if result == True and webhookUrl is not None:
        webhookAuth=None
        if webhookUsername is not None or webhookPassword is not None:
            webhookAuth=(webhookUsername, webhookPassword)

        logger.info('Forward data using Webhook')
        try:
            r = requests.post(webhookUrl, headers={'Content-type': 'application/json', 'Authorization': 'Basic '+os.getenv('AuthHeader')}, data=json.dumps(data))
            logger.debug('Success!')
            logger.debug(r)
            httpResult={
                'statusCode': r.status_code,
                'body': r.text
            }
        except requests.exceptions.RequestException as e:
            logger.debug('Request failed')
            logger.debug(e)
            httpResult={
                'statusCode': 500,
                'body': 'Can not connect to remote server ' + webhookUrl
            }
    else:
        logger.info('Do not forward data')
        httpResult={
            'statusCode': 200,
            'body': "Message not forwarded"
        }

    logger.info('Result: ' + str(httpResult))
    logger.info('End processing message!')

    return httpResult

def load_parameter(event, parameter):
    queryStringParameters=event.get('queryStringParameters')
    if queryStringParameters is None:
        r=os.getenv(parameter)
    else:
        r=queryStringParameters.get(parameter)
        if r is None:
            r=os.getenv(parameter)
    return r
    
def parse_json(input):
    if isinstance(input, dict):
        return input
    else:
        return json.loads(input)

def eval_filter(filter, data):
    operator=filter.get('operator')

    if operator == 'equals':
        return eval_equals(filter, data)
    elif operator == 'contains':
        return eval_contains(filter, data)
    elif operator == 'in':
        return eval_in(filter, data)
    elif operator == 'not':
        return eval_not(filter, data)
    elif operator == 'and':
        return eval_and(filter, data)
    elif operator == 'or':
        return eval_or(filter, data)
    elif operator == 'true':
        return True
    elif operator == 'false':
        return False
    else:
        raise Exception("Operator " + str(operator) + " not implemented")

#More intelligent data retrieval, used for parsing filter and ensuring the filter is configured correctly
def getJsonAttributeAndValidate(dataPayload, attribute):
    result=dataPayload.get(attribute)
    if result is None:
        raise Exception("Attribute \"" + attribute + "\" not found in payload: " + str(dataPayload))
    return result

def getField(field, data):
    #No data, return none
    if data is None:
        return None

    #Data is not a json object, return none
    if not isinstance(data, dict):
        return None
        
    dotPos=field.find(".")
    if dotPos < 0:
        return data.get(field)
    else:
        firstField=field[0:dotPos]
        remainingField=field[dotPos+1:]
        return getField(remainingField, data.get(firstField))

def eval_equals(filter, data):
    field=getJsonAttributeAndValidate(filter, 'field')
    expectedValue=getJsonAttributeAndValidate(filter, 'value')
    actualValue=getField(field, data)
    return expectedValue == actualValue

def eval_contains(filter, data):
    field=getJsonAttributeAndValidate(filter, 'field')
    expectedValue=getJsonAttributeAndValidate(filter, 'value')
    actualValue=getField(field, data)
    
    if actualValue is None:
        return False
    else:
        return expectedValue in actualValue

def eval_in(filter, data):
    field=getJsonAttributeAndValidate(filter, 'field')
    expectedValues=getJsonAttributeAndValidate(filter, 'values')
    actualValue=data.get(field)
    for v in expectedValues:
       if v == actualValue:
           return True
    return False

def eval_not(filter, data):
    f=getJsonAttributeAndValidate(filter, 'filter')
    return not eval_filter(f, data)

def eval_and(filter, data):
    filters=getJsonAttributeAndValidate(filter, 'filters')
    for f in filters:
       if not eval_filter(f, data):
           return False
    return True
    
def eval_or(filter, data):
    filters=getJsonAttributeAndValidate(filter, 'filters')
    for f in filters:
       if eval_filter(f, data):
           return True
    return False