import requests
import os
import config

def download_file(url, output_path):
    """Utility to download a file with a progress indicator."""
    print(f"Downloading from {url} to {output_path}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Download complete.")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def search_and_download_video(query, output_path):
    """
    Queries Pexels for a vertical video using the query string.
    Falls back to a default abstract video if API key is not configured or search fails.
    """
    # Check if API Key is configured
    if not config.PEXELS_API_KEY or config.PEXELS_API_KEY == "YOUR_PEXELS_API_KEY_HERE":
        print("Pexels API Key is not set. Falling back to default background video...")
        return download_fallback_video(output_path)

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",  # Request vertical videos
        "per_page": 5,
        "size": "medium"
    }

    try:
        print(f"Searching Pexels for vertical video with query: '{query}'...")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 401:
            print("Pexels API unauthorized (Invalid Key). Using fallback video...")
            return download_fallback_video(output_path)
            
        response.raise_for_status()
        data = response.json()
        
        videos = data.get("videos", [])
        if not videos:
            print(f"No vertical videos found for query '{query}'. Trying generic search...")
            params["query"] = "abstract background"
            response = requests.get(url, headers=headers, params=params, timeout=15)
            data = response.json()
            videos = data.get("videos", [])
            
        if videos:
            # Look for a suitable HD file
            video = videos[0]
            video_files = video.get("video_files", [])
            
            # Find an HD vertical file
            video_url = None
            for f in video_files:
                # Vertical constraint
                if f.get("width", 0) < f.get("height", 0):
                    # We prefer HD or SD
                    if f.get("quality") == "hd":
                        video_url = f.get("link")
                        break
            
            # Fallback to any file if no HD vertical found
            if not video_url and video_files:
                video_url = video_files[0].get("link")
                
            if video_url:
                return download_file(video_url, output_path)
            
        print("Could not find any suitable video links on Pexels. Using fallback...")
        return download_fallback_video(output_path)

    except Exception as e:
        print(f"Pexels search error: {e}. Using fallback...")
        return download_fallback_video(output_path)

def download_fallback_video(output_path):
    """Downloads a reliable default vertical stock video or image for fallback."""
    import random
    fallbacks = [
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=1080&h=1920&fit=crop", # Fashion model posing
        "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=1080&h=1920&fit=crop", # Beautiful model studio
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=1080&h=1920&fit=crop", # Model portrait nature
        "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=1080&h=1920&fit=crop", # Dancing model
        "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=1080&h=1920&fit=crop"  # High-fashion pose
    ]
    fallback_url = random.choice(fallbacks)
    print(f"Selected fallback image: {fallback_url}")
    return download_file(fallback_url, output_path)

if __name__ == "__main__":
    # Test downloader locally
    test_query = "nature forest"
    test_out = "test_video.mp4"
    search_and_download_video(test_query, test_out)
    
    # Cleanup test files if they exist
    if os.path.exists(test_out):
        os.remove(test_out)
