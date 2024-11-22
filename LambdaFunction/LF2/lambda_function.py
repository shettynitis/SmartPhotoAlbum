import json
from opensearchpy import OpenSearch, RequestsHttpConnection
import boto3

# OpenSearch (ElasticSearch) configuration
ELASTICSEARCH_ENDPOINT = "https://search-photos-2ghhsjv3273wh3sfklasdwuxni.us-east-1.es.amazonaws.com"
INDEX_NAME = "photos"

# Initialize OpenSearch client
es_client = OpenSearch(
    hosts=[{'host': 'search-photos-2ghhsjv3273wh3sfklasdwuxni.us-east-1.es.amazonaws.com', 'port': 443}],
    http_auth=('NitishaShetty', 'Password@98'),  # Replace with your credentials
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# Initialize Lex client
lex_client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    try:
        # Determine the source of the request (API Gateway or Lex)
        if 'queryStringParameters' in event:  # API Gateway request
            query = event.get('queryStringParameters', {}).get('q', None)
            
            if not query:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"message": "Missing query parameter 'q'."})
                }

            # Call Lex RecognizeText API to extract keywords/intents
            lex_response = lex_client.recognize_text(
                botId='YDIKJ9GWQN',             # Replace with your Lex bot ID
                botAliasId='TSTALIASID',  # Replace with your Lex bot alias ID
                localeId='en_US',
                sessionId='test_session',
                text=query
            )

            # Extract slots (keywords) from Lex response
            slots = lex_response.get('sessionState', {}).get('intent', {}).get('slots', {})
            keywords = []
            for slot_name, slot_value in slots.items():
                if slot_value and 'value' in slot_value:
                    keywords.append(slot_value['value']['interpretedValue'])
            query = ' '.join(keywords) if keywords else query  # Use extracted keywords or original query
        
        elif 'sessionState' in event:  # Amazon Lex request
            query = event['sessionState']['intent']['slots']['Keywords']['value']['interpretedValue']
            
            if not query:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "Close"
                        },
                        "intent": {
                            "name": event['sessionState']['intent']['name'],
                            "state": "Failed"
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": "Sorry, I couldn't process your request. Please provide a query."
                        }
                    ]
                }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid event structure."})
            }

        # Search the OpenSearch index
        response = es_client.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["labels"]
                    }
                }
            }
        )

        # Format the search results
        photos = []
        for hit in response['hits']['hits']:
            photos.append({
                "objectKey": hit['_source']['objectKey'],
                "bucket": hit['_source']['bucket'],
                "createdTimestamp": hit['_source']['createdTimestamp'],
                "labels": hit['_source']['labels']
            })

        # Construct the response
        if photos:
            message_content = f"I found the following photos for your query '{query}':\n" + \
                              "\n".join([photo['objectKey'] for photo in photos])
        else:
            message_content = f"Sorry, I couldn't find any photos matching your query '{query}'."

        # Return response based on source
        if 'queryStringParameters' in event:  # API Gateway
            return {
                "statusCode": 200,
                "body": json.dumps(photos)
            }
        else:  # Amazon Lex
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "Close"
                    },
                    "intent": {
                        "name": event['sessionState']['intent']['name'],
                        "state": "Fulfilled"
                    }
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": message_content
                    }
                ]
            }

    except Exception as e:
        print(f"Error: {e}")
        if 'queryStringParameters' in event:  # API Gateway
            return {
                "statusCode": 500,
                "body": json.dumps({"message": f"An error occurred: {str(e)}"})
            }
        else:  # Amazon Lex
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "Close"
                    },
                    "intent": {
                        "name": event['sessionState']['intent']['name'],
                        "state": "Failed"
                    }
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": f"An error occurred: {str(e)}"
                    }
                ]
            }
