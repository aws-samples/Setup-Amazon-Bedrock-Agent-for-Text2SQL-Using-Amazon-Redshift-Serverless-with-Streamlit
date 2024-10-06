import json
import os
from redshift_serverless_functions import get_schema, get_user_acl, execute_query

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    try:
        api_path = event.get('apiPath')
        if not api_path:
            return format_error_response('Missing apiPath in event', event)

        if api_path == "/getschema":
            properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
            db = next((prop['value'] for prop in properties if prop['name'] == 'db'), None)
            if db is None:
                return format_error_response('Missing database parameter', event)
            result = get_schema(db)

        elif api_path == "/querydatabase":
            properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
            user_id = next((prop['value'] for prop in properties if prop['name'] == 'user_id'), None)
            db = next((prop['value'] for prop in properties if prop['name'] == 'database'), None)
            schema = next((prop['value'] for prop in properties if prop['name'] == 'schema'), None)
            table = next((prop['value'] for prop in properties if prop['name'] == 'table'), None)
            query = next((prop['value'] for prop in properties if prop['name'] == 'query'), None)
            
            if not all([db, schema, query]):
                return format_error_response('Missing required parameters', event)
            
            result = execute_query(query, db, schema, table, user_id)
            print("Query Result:", result)  # Debug print

        elif api_path == "/getUserACL":
            properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
            user_id = next((prop['value'] for prop in properties if prop['name'] == 'user_id'), None)
            if user_id is None:
                return format_error_response('Missing user_id parameter', event)
            result = get_user_acl(user_id)

        else:
            return format_error_response('Invalid API path', event)

        return format_success_response(result, event)

    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return format_error_response(str(e), event)

def format_error_response(error_message, event):
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup', 'DefaultActionGroup'),
            'apiPath': event.get('apiPath', '/unknown'),
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': 400,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({'error': error_message})
                }
            }
        }
    }

def format_success_response(result, event):
    if result is None:
        result = {"error": "Query returned no results."}
    elif isinstance(result, str) and result.startswith("Error:"):
        return format_error_response(result, event)
    
    result_str = json.dumps(result)
    if len(result_str) > 24000:  # Check if result exceeds Bedrock's 25 KB limit
        result = {"error": "Response size exceeds 25 KB limit."}

    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup', 'DefaultActionGroup'),
            'apiPath': event.get('apiPath', '/unknown'),
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
        },
        'sessionAttributes': event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }