import os
import sys
import shutil
import asyncio
import requests
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
import config
from youtube_uploader import upload_short_video

# Force UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def download_file(url, output_path):
    print(f"Downloading {url} to {output_path}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, stream=True, timeout=30)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print("Download complete.")

# Registry of supported joke video metadata
JOKE_REGISTRY = {
    "auto_correct": {
        "file_keyword": "auto_correct",
        "title": "Auto Correct ने मेरी इज्जत करेक्ट कर दी! 😂 #shorts #standup #comedy",
        "desc": "Funny Hindi Stand-Up Comedy Short about Auto Correct. #shorts #comedy #standup #hindi #viral",
        "tags": ["shorts", "standup", "comedy", "hindi", "autocorrect", "funny"]
    },
    "screenshot": {
        "file_keyword": "1037",
        "title": "गलती से पूरी Gallery भेज दी! 📸😂 #shorts #standup #comedy",
        "desc": "Relatable daily life comedy Short about screenshots and sending the wrong files. #shorts #comedy #standup #hindi",
        "tags": ["shorts", "standup", "comedy", "hindi", "screenshot", "gallery"]
    },
    "google": {
        "file_keyword": "1107",
        "title": "Google Search करने का नतीजा! 🩺😂 #shorts #standup #comedy",
        "desc": "Relatable Hindi comedy short about searching symptoms on Google. #shorts #comedy #standup #hindi",
        "tags": ["shorts", "standup", "comedy", "hindi", "google", "doctor"]
    },
    "calculator": {
        "file_keyword": "1113",
        "title": "2+2 Confirm करने की आदत! 🧮😂 #shorts #standup #comedy",
        "desc": "Funny relatable standup comedy short about overusing calculators. #shorts #comedy #standup #hindi",
        "tags": ["shorts", "standup", "comedy", "hindi", "calculator", "math"]
    }
}

async def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_standup_by_name.py [auto_correct|screenshot|google|calculator]")
        return
        
    joke_key = sys.argv[1].lower()
    if joke_key not in JOKE_REGISTRY:
        print(f"Error: Joke '{joke_key}' not found in registry. Choose from: {list(JOKE_REGISTRY.keys())}")
        return
        
    joke_meta = JOKE_REGISTRY[joke_key]
    keyword = joke_meta["file_keyword"]
    
    print("="*60)
    print(f"Generating Video for: {joke_key.upper()}")
    print(f"Title: {joke_meta['title']}")
    print("="*60)

    # Ensure directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # Find the target video in Downloads folder
    downloads_dir = r"C:\Users\VSRM COMPUTER CLASS\Downloads"
    bg_video_path = None
    if os.path.exists(downloads_dir):
        for f in os.listdir(downloads_dir):
            if keyword in f and f.endswith(".mp4"):
                bg_video_path = os.path.join(downloads_dir, f)
                break

    if not bg_video_path or not os.path.exists(bg_video_path):
        print(f"Error: Pre-generated video containing '{keyword}' not found in Downloads folder.")
        return

    laughter_audio = os.path.join("temp", "laughter.mp3")
    applause_audio = os.path.join("temp", "applause.mp3")
    final_output = os.path.join("output", f"standup_{joke_key}.mp4")

    # 1. Download Sound Effects
    try:
        download_file("https://github.com/jitsi/jitsi-meet/raw/master/sounds/reactions-laughter.mp3", laughter_audio)
        download_file("https://github.com/jitsi/jitsi-meet/raw/master/sounds/reactions-applause.mp3", applause_audio)
    except Exception as e:
        print(f"Error downloading reaction sounds: {e}")
        return

    # 2. Load Clips (with watermark removal zoom crop & sample-accurate audio loading)
    print(f"Loading video: {bg_video_path}")
    bg_clip_raw = VideoFileClip(bg_video_path)
    
    # Zoom by 22% and crop shifted up by 50px to completely remove the Gemini star watermark
    zoomed = bg_clip_raw.resized(1.22)
    new_w, new_h = zoomed.size
    x1 = (new_w - 1080) // 2
    y1 = ((new_h - 1920) // 2) - 50
    bg_clip = zoomed.cropped(x1=x1, y1=y1, width=1080, height=1920).without_audio()
    
    # Load audio directly to prevent seek clipping
    voice_clip = AudioFileClip(bg_video_path)
    duration = bg_clip.duration

    # 3. Mix Reaction Audio Timing (laughter starts mid-way, applause at the end)
    laughter_start = 3.5
    applause_start = 7.0

    audience_laugh = AudioFileClip(laughter_audio).with_start(laughter_start).with_volume_scaled(0.35)
    audience_app = AudioFileClip(applause_audio).with_start(applause_start).with_volume_scaled(0.25)

    mixed_audio = CompositeAudioClip([
        voice_clip,
        audience_laugh,
        audience_app
    ]).with_duration(duration)

    # 4. Composite Video
    video = CompositeVideoClip([bg_clip]).with_duration(duration)
    video = video.with_audio(mixed_audio)

    # 5. Export Video
    print(f"Rendering final video to {final_output}...")
    video.write_videofile(
        final_output,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        temp_audiofile=os.path.join("temp", "temp-audio.m4a"),
        remove_temp=True
    )
    print("Video rendering complete!")

    # Close clips
    audience_laugh.close()
    audience_app.close()
    bg_clip.close()
    voice_clip.close()
    video.close()

    # 6. Upload to YouTube
    print(f"Uploading stand-up comedy Short '{joke_key}' to YouTube...")
    video_id = upload_short_video(final_output, joke_meta["title"], joke_meta["desc"], joke_meta["tags"])
    if video_id:
        print(f"SUCCESS: Video successfully published to YouTube! ID: {video_id}")
    else:
        print("ERROR: YouTube upload failed.")

    # Cleanup temp directory
    try:
        shutil.rmtree("temp")
        print("Cleaned up temp directory.")
    except Exception as e:
        print(f"Error cleaning up: {e}")

if __name__ == "__main__":
    asyncio.run(main())
