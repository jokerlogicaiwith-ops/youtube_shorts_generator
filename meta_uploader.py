import os
import time
import requests

def upload_to_catbox(file_path):
    """
    Uploads a video to Catbox.moe for temporary public hosting.
    Meta API requires a direct public URL to download the video.
    """
    print("Uploading video to Catbox for temporary public hosting...")
    url = "https://catbox.moe/user/api.php"
    data = {
        "reqtype": "fileupload",
    }
    try:
        with open(file_path, "rb") as f:
            files = {"fileToUpload": f}
            r = requests.post(url, data=data, files=files, timeout=60)
        if r.status_code == 200:
            public_url = r.text.strip()
            print(f"Catbox public URL: {public_url}")
            return public_url
        else:
            print(f"Catbox upload failed: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"Error uploading to Catbox: {e}")
        return None

def upload_to_uguu(file_path):
    """
    Uploads a file to uguu.se for temporary public hosting.
    Uguu keeps files for 24 hours.
    """
    print("Uploading video to uguu.se for temporary public hosting...")
    try:
        url = "https://uguu.se/upload"
        with open(file_path, "rb") as f:
            files = {"files[]": f}
            r = requests.post(url, files=files, timeout=60)
        if r.status_code == 200:
            res = r.json()
            if res.get("success"):
                public_url = res.get("files")[0].get("url")
                print(f"Uguu.se public URL: {public_url}")
                return public_url
        print(f"Uguu.se upload failed: {r.status_code} - {r.text}")
        return None
    except Exception as e:
        print(f"Error uploading to Uguu.se: {e}")
        return None

def upload_to_file_io(file_path):
    """
    Uploads a video to file.io as a fallback.
    """
    print("Uploading video to file.io for temporary public hosting...")
    try:
        url = "https://file.io"
        with open(file_path, "rb") as f:
            files = {"file": f}
            r = requests.post(url, files=files, timeout=60)
        if r.status_code == 200:
            res = r.json()
            if res.get("success"):
                public_url = res.get("link")
                print(f"file.io public URL: {public_url}")
                return public_url
        print(f"file.io upload failed: {r.status_code} - {r.text}")
        return None
    except Exception as e:
        print(f"Error uploading to file.io: {e}")
        return None

def get_temporary_public_url(file_path):
    """
    Tries to upload the video to Uguu.se, Catbox, or file.io sequentially.
    """
    # 1. Try Uguu.se (Most reliable across Cloud / Local networks)
    url = upload_to_uguu(file_path)
    if url:
        return url
        
    # 2. Try Catbox
    url = upload_to_catbox(file_path)
    if url:
        return url
        
    # 3. Try file.io
    url = upload_to_file_io(file_path)
    if url:
        return url
        
    return None

def upload_instagram_reels(video_url, caption, access_token, instagram_account_id):
    """
    Uploads the video to Instagram Reels using the Meta Graph API.
    """
    if not access_token or access_token == "YOUR_META_ACCESS_TOKEN_HERE":
        print("Instagram Access Token is not configured. Skipping Instagram upload.")
        return False
    if not instagram_account_id or instagram_account_id == "YOUR_INSTAGRAM_ACCOUNT_ID_HERE":
        print("Instagram Account ID is not configured. Skipping Instagram upload.")
        return False
        
    print("Initiating Instagram Reels upload...")
    url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token
    }
    
    try:
        r = requests.post(url, data=payload, timeout=30)
        if r.status_code != 200:
            print(f"Failed to create Instagram media container: {r.text}")
            return False
            
        container_id = r.json().get("id")
        print(f"Instagram container created successfully with ID: {container_id}")
        
        # Poll status of the container
        poll_url = f"https://graph.facebook.com/v19.0/{container_id}"
        poll_params = {
            "fields": "status_code,failure_reason",
            "access_token": access_token
        }
        
        print("Waiting for Instagram to finish processing the video (polling)...")
        max_attempts = 20
        processing_complete = False
        
        for attempt in range(max_attempts):
            time.sleep(15)  # Wait 15 seconds
            pr = requests.get(poll_url, params=poll_params, timeout=15)
            if pr.status_code == 200:
                data = pr.json()
                status = data.get("status_code")
                print(f"Attempt {attempt+1}/{max_attempts} - Status: {status}")
                if status == "FINISHED":
                    processing_complete = True
                    break
                elif status == "ERROR":
                    reason = data.get("failure_reason", "unknown reason")
                    print(f"Instagram processing failed: {reason}")
                    return False
            else:
                print(f"Error checking container status: {pr.text}")
                
        if not processing_complete:
            print("Instagram video processing timed out. Skipping publish.")
            return False
            
        # Publish container
        publish_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token
        }
        pub_res = requests.post(publish_url, data=publish_payload, timeout=30)
        if pub_res.status_code == 200:
            post_id = pub_res.json().get("id")
            print(f"SUCCESS: Video published to Instagram Reels! Post ID: {post_id}")
            return True
        else:
            print(f"Failed to publish Instagram Reels: {pub_res.text}")
            return False
            
    except Exception as e:
        print(f"Error during Instagram upload: {e}")
        return False

def upload_facebook_reels(video_url, description, access_token, page_id):
    """
    Uploads the video to Facebook Reels on the specified Page.
    """
    if not access_token or access_token == "YOUR_META_ACCESS_TOKEN_HERE":
        print("Facebook Access Token is not configured. Skipping Facebook upload.")
        return False
    if not page_id or page_id == "YOUR_FACEBOOK_PAGE_ID_HERE":
        print("Facebook Page ID is not configured. Skipping Facebook upload.")
        return False

    print("Initiating Facebook Reels upload...")
    try:
        # Step 1: Start video reels upload
        url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
        payload = {
            "upload_phase": "start",
            "access_token": access_token
        }
        r = requests.post(url, data=payload, timeout=30)
        if r.status_code != 200:
            print(f"Failed to initialize Facebook Reels upload: {r.text}")
            return False
            
        res_data = r.json()
        video_id = res_data.get("video_id")
        upload_url = res_data.get("upload_url")
        
        # Step 2: Push the video URL to Facebook upload endpoint
        headers = {
            "Authorization": f"OAuth {access_token}",
            "file_url": video_url
        }
        upload_res = requests.post(upload_url, headers=headers, timeout=30)
        if upload_res.status_code not in [200, 201]:
            print(f"Failed to upload video from URL to Facebook: {upload_res.text}")
            return False
            
        # Step 3: Finish the upload session and publish
        finish_url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
        finish_payload = {
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description,
            "access_token": access_token
        }
        finish_res = requests.post(finish_url, data=finish_payload, timeout=30)
        if finish_res.status_code == 200:
            print(f"SUCCESS: Video published to Facebook Reels! Video ID: {video_id}")
            return True
        else:
            print(f"Failed to publish Facebook Reels: {finish_res.text}")
            return False

    except Exception as e:
        print(f"Error during Facebook upload: {e}")
        return False

def upload_to_meta(file_path, caption):
    """
    Main function to run both Instagram and Facebook uploads.
    Fetches credentials from environment variables.
    """
    access_token = os.environ.get("META_ACCESS_TOKEN")
    instagram_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    
    if not access_token:
        print("Meta Access Token is not set in environment. Skipping Meta uploads.")
        return
        
    print("\n" + "="*50)
    print("Meta (Instagram & Facebook) Reels Auto-Uploader")
    print("="*50)
    
    # 1. Upload to temporary public hosting
    public_url = get_temporary_public_url(file_path)
    if not public_url:
        print("Skipping Meta uploads because temporary public hosting failed.")
        return
        
    # 2. Upload to Instagram
    if instagram_id:
        upload_instagram_reels(public_url, caption, access_token, instagram_id)
        
    # 3. Upload to Facebook
    if page_id:
        upload_facebook_reels(public_url, caption, access_token, page_id)
    print("="*50 + "\n")
