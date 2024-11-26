import json
import boto3
import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection

# AWS services
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')
code_pipeline_client = boto3.client('codepipeline')

# ElasticSearch (OpenSearch) configuration
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

def process_s3_event(event):
    # Handles S3 event for label detection and indexing in OpenSearch
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # Detect labels using Rekognition
    rekognition_response = rekognition_client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_key
            }
        },
        MaxLabels=10
    )
    labels = [label['Name'] for label in rekognition_response['Labels']]

    # Retrieve custom metadata from S3
    metadata_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
    custom_labels = metadata_response['Metadata'].get('customlabels', '')
    custom_labels_list = custom_labels.split(',') if custom_labels else []

    # Combine Rekognition and custom labels
    all_labels = labels + custom_labels_list

    # Create the JSON object
    photo_metadata = {
        "objectKey": object_key,
        "bucket": bucket_name,
        "createdTimestamp": datetime.datetime.now().isoformat(),
        "labels": all_labels
    }

    # Index the JSON object in OpenSearch
    es_client.index(index=INDEX_NAME, body=photo_metadata, id=object_key)

    return "Photo indexed successfully!"


def process_codepipeline_event(event):
    # Handles CodePipeline event to signal success or failure.
    job_id = event['CodePipeline.job']['id']
    code_pipeline_client.put_job_success_result(jobId=job_id)


def lambda_handler(event, context):
    try:
        # Check the source of the event
        if 'Records' in event:  # S3 event
            result = process_s3_event(event)
            return {
                "statusCode": 200,
                "body": json.dumps(result)
            }
        elif 'CodePipeline.job' in event:  # CodePipeline event
            process_codepipeline_event(event)
            return {
                "statusCode": 200,
                "body": json.dumps("CodePipeline job processed successfully!")
            }
        else:
            raise ValueError("Unrecognized event structure")

    except Exception as e:
        print(f"Error: {e}")
        if 'CodePipeline.job' in event:
            job_id = event['CodePipeline.job']['id']
            code_pipeline_client.put_job_failure_result(jobId=job_id, failureDetails={
                'type': 'JobFailed',
                'message': str(e)
            })
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error: {str(e)}")
        }
