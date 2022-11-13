import json

# import requests


def lambda_handler(event, context):
    print(json.dumps(event, indent=2))
    for rec in event['Records']:
        print('file_name=' + rec['s3']['object']['key'])
        print('bucket_name=' + rec['s3']['bucket']['name'])
