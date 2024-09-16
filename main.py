import googleapiclient.discovery
import google_auth_httplib2
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json
import os
from datetime import date



SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "credential.json"
TOKEN_FILE = "token.json"

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
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=8082)
        store_auth_auth_code_token(creds)  
    return creds


def main():
    credentials_api = get_authenticated_service()
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials_api)

    todaydate = date.today()
    todaydate = str(todaydate)
    todaydate = todaydate[-2::]


    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Upload video test1",
                "description": "Upload video test1 description",
                "tags": ["sample", "video", "upload"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body= f"./Videos/{todaydate}.mp4"
    )

    response = request.execute()
    print(f"Video uploaded successfully: {response}")

if __name__ == "__main__":
    main()






