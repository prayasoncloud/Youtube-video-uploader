import googleapiclient.discovery
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json
import os
from datetime import date
import requests

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "credential.json"
TOKEN_FILE = "token.json"
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2-2b-it"
API_TOKEN = os.getenv('THE_API_TOKEN')


#Auth2.0
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


headers = {"Authorization": f"Bearer {API_TOKEN}"}

#Hugging Face 
def generate_description(text):
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


# input_text = "Jogging in the park"
# description = generate_description(input_text)
# print(description)



def main():
    credentials_api = get_authenticated_service()
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials_api)

    todaydate = date.today()
    todaydate = str(todaydate)
    todaydate = todaydate[-2::]
#--


    directory_path = r'C:\Users\prayas.patel\Desktop\YT-video-automation\Videos'
    name_of_the_video = ""

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        name_of_the_video += filename[:-4:]
        break

    description_of_the = generate_description(name_of_the_video)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{filename}",
                "description": f"{description_of_the}",
                "tags": ["1", "2", "thee"], 
                "categoryId": "1"
            },
            "status": {
                "privacyStatus": "private"
            }
        },
        media_body= file_path
    )
   
    response = request.execute()
    print(f"Video uploaded successfully: {response}")


    os.remove(file_path)

if __name__ == "__main__":
    main()






