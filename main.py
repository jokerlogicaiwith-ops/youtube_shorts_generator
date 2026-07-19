import os
import sys
import random
import time

# Force UTF-8 encoding for standard output and error to support emojis on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from datetime import datetime
import config
from script_generator import generate_script
from audio_generator import generate_audio_and_subtitles
from media_downloader import search_and_download_video, download_file
from video_editor import assemble_video
from youtube_uploader import upload_short_video

# Free royalty-free background music track URL (upbeat pop track)
FREE_MUSIC_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"  # Upbeat test audio

def get_next_topic():
    """
    Selects the next topic in rotation or picks a random one.
    Uses a local index.txt file to keep track of rotation.
    If running in GitHub Actions (non-persistent environment), picks a random topic.
    """
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("Running in GitHub Actions environment. Selecting a random topic to avoid repetition...")
        return random.choice(config.TOPICS)

    state_file = "last_topic_index.txt"
    if not os.path.exists(state_file):
        with open(state_file, "w") as f:
            f.write("0")
        return config.TOPICS[0]

    try:
        with open(state_file, "r") as f:
            idx = int(f.read().strip())
        next_idx = (idx + 1) % len(config.TOPICS)
        with open(state_file, "w") as f:
            f.write(str(next_idx))
        return config.TOPICS[next_idx]
    except Exception:
        # Fallback to random choice
        return random.choice(config.TOPICS)

def main():
    print("="*60)
    print(f"YouTube Shorts Auto-Generator & Uploader - Starting Run at {datetime.now()}")
    print("="*60)

    # 1. Topic selection
    if len(sys.argv) > 1:
        # User passed a custom topic as command-line argument
        topic = " ".join(sys.argv[1:])
        print(f"Using custom topic from argument: '{topic}'")
    else:
        topic = get_next_topic()
        print(f"Using topic from daily rotation: '{topic}'")

    # Ensure directories exist
    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    # Define file paths
    temp_audio = os.path.join("temp", "voice.mp3")
    temp_subs = os.path.join("temp", "subtitles.srt")
    temp_video = os.path.join("temp", "bg_video.mp4")
    music_file = "background_music.mp3"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output = os.path.join("output", f"short_{timestamp}.mp4")

    # 2. Download background music if not exists
    if not os.path.exists(music_file):
        print("Downloading free background music...")
        # Soundhelix tracks are free to use. Let's download a small track
        success = download_file(FREE_MUSIC_URL, music_file)
        if not success:
            print("Failed to download music. Proceeding without background music.")
            music_file = None

    # 3. Generate script via Gemini API
    try:
        data = generate_script(topic)
        title = data.get("title", f"Amazing Facts About {topic}")
        description = data.get("description", "Daily short facts. #shorts #facts")
        query = data.get("pexels_query", topic)
        paragraphs = data.get("script_paragraphs", [])
        
        script_text = " ".join(paragraphs)
        
        print("\n--- GENERATED DETAILS ---")
        print(f"Title: {title}")
        print(f"Pexels Query: {query}")
        print(f"Full Script: {script_text}")
        print("-------------------------\n")
        
    except Exception as e:
        print(f"CRITICAL ERROR generating script: {e}")
        return

    # 4. Generate Voiceover Audio & Subtitles
    print("Generating voiceover audio...")
    audio_success = generate_audio_and_subtitles(script_text, temp_audio, temp_subs)
    if not audio_success:
        print("CRITICAL ERROR: Failed to generate audio. Aborting.")
        return

    # 5. Download Background Video Clip
    print("Searching and downloading background video...")
    video_success = search_and_download_video(query, temp_video)
    if not video_success:
        print("CRITICAL ERROR: Failed to download background video. Aborting.")
        return

    # 6. Assemble Video (Mix audio, video, subtitles, music)
    try:
        assemble_video(
            video_path=temp_video,
            audio_path=temp_audio,
            srt_path=temp_subs,
            output_path=final_output,
            music_path=music_file if os.path.exists(music_file) else None
        )
    except Exception as e:
        print(f"CRITICAL ERROR assembling video: {e}")
        return

    # 7. Upload to YouTube
    print("\nStarting upload to YouTube...")
    try:
        video_id = upload_short_video(
            video_path=final_output,
            title=title,
            description=description,
            tags=["shorts", "facts", "youtube", "viral"]
        )
        if video_id:
            print(f"SUCCESS: Video successfully published to YouTube! ID: {video_id}")
        else:
            print("WARNING: YouTube upload was skipped or failed. Video remains saved locally.")
    except Exception as e:
        print(f"Error uploading video: {e}")

    # 8. Clean up temp folder
    print("Cleaning up temporary files...")
    for f in [temp_audio, temp_subs, temp_video]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception as e:
                print(f"Error deleting temp file {f}: {e}")

    print(f"\nWorkflow complete! Generated video is available at: {os.path.abspath(final_output)}")
    print("="*60)

if __name__ == "__main__":
    main()
