import os
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import config

# Scopes needed for uploading videos and managing playlists
SCOPES = ["https://www.googleapis.com/auth/youtube"]

def get_authenticated_service():
    """
    Authenticates the user and returns the YouTube service client.
    First-time run will open a web browser to request permissions.
    """
    credentials = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(config.TOKEN_FILE):
        from google.oauth2.credentials import Credentials
        try:
            credentials = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading saved token: {e}. Re-authenticating...")

    # If there are no valid credentials, let the user log in.
    if not credentials or not credentials.valid:
        from google.auth.transport.requests import Request
        if credentials and credentials.expired and credentials.refresh_token:
            print("Token expired. Refreshing token...")
            try:
                credentials.refresh(Request())
            except Exception as e:
                print(f"Refresh failed: {e}. Needs full authentication.")
                credentials = None
                
        if not credentials:
            if not os.path.exists(config.CLIENT_SECRET_FILE):
                print("\n" + "="*60)
                print("WARNING: client_secret.json was not found in the project directory.")
                print("To upload videos to YouTube automatically, you must:")
                print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
                print("2. Create a project and enable 'YouTube Data API v3'.")
                print("3. Create 'OAuth 2.0 Client IDs' (Desktop application type).")
                print("4. Download the JSON credentials file and rename it to 'client_secret.json'")
                print("   and place it in this directory:")
                print(f"   {os.path.abspath(config.CLIENT_SECRET_FILE)}")
                print("="*60 + "\n")
                return None
                
            from google_auth_oauthlib.flow import InstalledAppFlow
            print("Opening browser for YouTube authorization. Please complete the login in your browser...")
            flow = InstalledAppFlow.from_client_secrets_file(config.CLIENT_SECRET_FILE, SCOPES)
            credentials = flow.run_local_server(port=0, open_browser=False)
            
        # Save credentials for future runs
        with open(config.TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())
            print(f"Saved authorization credentials to {config.TOKEN_FILE}")

    return build("youtube", "v3", credentials=credentials)

def add_video_to_playlist(youtube, video_id, playlist_title="Funny"):
    """
    Finds or creates a playlist with the given title, and adds the video to it.
    """
    try:
        playlist_id = None
        # 1. Search for existing playlist
        print(f"Searching for existing playlist '{playlist_title}'...")
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        )
        response = request.execute()
        
        for item in response.get("items", []):
            if item["snippet"]["title"].strip().lower() == playlist_title.lower():
                playlist_id = item["id"]
                print(f"Found existing playlist '{playlist_title}' with ID: {playlist_id}")
                break
                
        # 2. If not found, create it
        if not playlist_id:
            print(f"Playlist '{playlist_title}' not found. Creating a new one...")
            playlists_insert_response = youtube.playlists().insert(
                part="snippet,status",
                body={
                  "snippet": {
                    "title": playlist_title,
                    "description": "Funny and comedy short videos generated automatically."
                  },
                  "status": {
                    "privacyStatus": "public"
                  }
                }
            ).execute()
            playlist_id = playlists_insert_response["id"]
            print(f"Created new playlist '{playlist_title}' with ID: {playlist_id}")
            
        # 3. Add video to the playlist
        print(f"Adding video {video_id} to playlist {playlist_title}...")
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        print(f"Successfully added video to playlist '{playlist_title}'!")
        return True
    except Exception as e:
        print(f"Failed to add video to playlist: {e}")
        return False

def upload_short_video(video_path, title, description, tags=None):
    """
    Uploads the video file to YouTube.
    """
    youtube = get_authenticated_service()
    if not youtube:
        print("Skipping YouTube upload because credentials are not configured.")
        return None

    print(f"Initiating YouTube upload for {video_path}...")
    
    # Ensure title contains #Shorts (YouTube requirement to index as Short easily)
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    body = {
        "snippet": {
            "title": title[:100],  # YouTube title limit is 100 chars
            "description": description,
            "tags": tags or ["shorts", "youtube", "facts"],
            "categoryId": "22"  # Category 22 is 'People & Blogs'
        },
        "status": {
            "privacyStatus": config.YOUTUBE_UPLOAD_STATUS,  # 'private', 'public', or 'unlisted'
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/*",
        chunksize=1024*1024,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    try:
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}% complete...")
        
        video_id = response.get("id")
        print(f"Upload Successful! Video ID: {video_id}")
        print(f"Watch Link: https://www.youtube.com/watch?v={video_id}")
        
        # Add video to "Funny" playlist
        add_video_to_playlist(youtube, video_id, "Funny")
        
        return video_id
        
    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} - {e.content}")
        return None
    except Exception as e:
        print(f"An error occurred during upload: {e}")
        return None

if __name__ == "__main__":
    # Test credentials setup (doesn't upload anything)
    print("Testing YouTube Authentication service...")
    service = get_authenticated_service()
    if service:
        print("YouTube Authentication Service Initialized Successfully!")
