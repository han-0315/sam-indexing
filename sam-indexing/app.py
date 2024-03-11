import json
import boto3
from google.oauth2 import service_account
import googleapiclient.discovery
import requests

# AWS Secret Manager에서 비밀을 가져오는 함수
def get_secret():
    secret_name = "googleAPI"
    region_name = "ap-northeast-2"

    # AWS Secret Manager 클라이언트 생성
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return json.loads(decoded_binary_secret)

# Google API를 인증하고 URL을 인덱싱하는 함수
def authenticate_and_notify(url):
    secret_info = get_secret()
    credentials = service_account.Credentials.from_service_account_info(secret_info, scopes=['https://www.googleapis.com/auth/indexing'])
    
    service = googleapiclient.discovery.build('indexing', 'v3', credentials=credentials)
    body = {
        'url': url,
        'type': 'URL_UPDATED'
    }
    response = service.urlNotifications().publish(body=body).execute()
    print('Response from Google Indexing API:', response)

# AWS Lambda 핸들러
def lambda_handler(event, lambda_context):
    print("Received event: ", event)
    try:
        # 이벤트에서 URL 가져오기
        url = event['Records'][0]['body']['data']
        print("URL from event:", url)
        authenticate_and_notify(url)
        return {
            'statusCode': 200,
            'body': json.dumps('URL Updated: ' + url)
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error updating URL')
        }
