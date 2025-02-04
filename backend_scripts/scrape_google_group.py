from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_credentials():
    """Gets credentials from environment variables."""
    try:
        creds = Credentials(
            token=os.getenv('GOOGLE_ACCESS_TOKEN'),
            refresh_token=os.getenv('GOOGLE_REFRESH_TOKEN'),
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            token_uri='https://oauth2.googleapis.com/token'
        )
        return creds
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None

def print_group_emails(group_id):
    """Prints all emails from a Google Group."""
    creds = get_credentials()
    if not creds:
        print("Failed to get credentials")
        return
        
    service = build('groupssettings', 'v1', credentials=creds)
    
    try:
        page_token = None
        email_count = 0
        
        while True:
            response = service.groups().list(
                groupKey=group_id,
                pageToken=page_token
            ).execute()
            
            messages = response.get('messages', [])
            for message in messages:
                email_count += 1
                print("\n" + "="*50 + f" Email #{email_count} " + "="*50)
                print(f"Subject: {message.get('subject', 'No subject')}")
                print(f"From: {message.get('from', 'No sender')}")
                print(f"Date: {message.get('date', 'No date')}")
                print("\nContent:")
                print(message.get('plainTextBody', 'No content'))
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        
        print(f"\nTotal emails found: {email_count}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    GROUP_ID = os.getenv('GOOGLE_GROUP_ID', 'default-group@googlegroups.com')
    print_group_emails(GROUP_ID) 