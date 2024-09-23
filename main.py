import googleapiclient.discovery
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json
import os
from datetime import date
import requests
import boto3
import random

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "credential.json"
TOKEN_FILE = "token.json"
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2-2b-it"
API_TOKEN = os.getenv("THE_API_TOKEN_HF")

S3_BUCKET_NAME = "youtube-uploader-123"  # Your S3 bucket name
S3_PREFIX = "Videos/"  # The folder inside your bucket

def store_auth_auth_code_token(creds):
    with open(TOKEN_FILE, "w") as token_file:
        json.dump(creds.to_json(), token_file)

def fetching_auth_code_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as token_file:
            creds_json = json.load(token_file)
        return Credentials.from_authorized_user_info(json.loads(creds_json), SCOPES)
    return None

def get_authenticated_service():
    creds = fetching_auth_code_token()
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8082)
        store_auth_auth_code_token(creds)
    
    return creds

def generate_description(text):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    payload = {
        "inputs": f"Write a YouTube video description for: {text}",
        "parameters": {"max_length": 90, "min_length": 50}
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        generated_text = response.json()[0]['generated_text']
        
        description_start = generated_text.find("Description:")
        if description_start != -1:
            return generated_text[description_start + len("Description:"):].strip()
        else:
            return generated_text.strip()
    else:
        return f"Error: {response.status_code}, {response.text}"

def list_files_in_s3():
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_PREFIX)

    if 'Contents' in response:
        files = [obj['Key'] for obj in response['Contents']]
        return files
    return []

def download_from_s3(file_name):
    s3 = boto3.client('s3')
    s3.download_file(S3_BUCKET_NAME, file_name, file_name)

def upload_to_youtube(file_path):
    credentials_api = get_authenticated_service()
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials_api)

    name_of_the_video = os.path.basename(file_path)[:-4]  # Get the video name without extension
    description_of_the = generate_description(name_of_the_video)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": name_of_the_video,
                "description": description_of_the,
                "tags": ["1", "2", "three"],
                "categoryId": "1"
            },
            "status": {
                "privacyStatus": "private"
            }
        },
        media_body=file_path
    )

    response = request.execute()
    print(f"Video uploaded successfully: {response}")

    s3.delete_object(Bucket=S3_BUCKET_NAME, Key=file_name)
    print(f"{file_name} deleted from S3.")

def main():
    # List files in the specified S3 directory
    files = list_files_in_s3()
    
    if not files:
        print("No files found in the S3 bucket.")
        return

    selected_file = random.choice(files)
    print(f"Selected file: {selected_file}")

    download_from_s3(selected_file)

    upload_to_youtube(selected_file)

    delete_from_s3(selected_file)

    if os.path.exists(selected_file):
        os.remove(selected_file)

if __name__ == "__main__":
    main()
