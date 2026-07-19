import os
import re
import shutil
import tempfile
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, CompositeAudioClip
import moviepy.video.fx as vfx
import config

def parse_srt(srt_path):
    """
    Parses an SRT file and returns a list of dictionaries with start, end, and text.
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Normalize line endings to LF to avoid matching issues with CRLF on Windows
    content = content.replace("\r\n", "\n")

    # Regex pattern to match SRT subtitles: index, timestamps, and text
    pattern = re.compile(
        r"\d+\s*\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\n|\n*$|\Z)",
        re.DOTALL
    )

    def time_to_seconds(t_str):
        # SRT timestamps use ',' for decimal separator
        t_str = t_str.replace(",", ".")
        parts = t_str.split(":")
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s

    matches = pattern.findall(content)
    subtitles = []
    for start_str, end_str, text in matches:
        subtitles.append({
            "start": time_to_seconds(start_str),
            "end": time_to_seconds(end_str),
            "text": text.strip()
        })
    return subtitles

def create_subtitle_image(text, output_path, width=config.VIDEO_WIDTH, height=config.VIDEO_HEIGHT):
    """
    Creates a transparent PNG with centered outline text.
    """
    # Create transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load Font
    try:
        font = ImageFont.truetype(config.FONT_PATH, config.FONT_SIZE)
    except IOError:
        print(f"Could not load font from {config.FONT_PATH}. Using default font.")
        font = ImageFont.load_default()

    # Get text dimensions (handle Pillow version differences)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older Pillow versions
        text_w, text_h = draw.textsize(text, font=font)

    # Position in center-bottom (about 65% down the screen)
    x = (width - text_w) // 2
    y = int(height * 0.65) - (text_h // 2)

    # Draw border/stroke for readability
    bw = config.BORDER_WIDTH
    if bw > 0:
        for dx in range(-bw, bw + 1):
            for dy in range(-bw, bw + 1):
                if dx*dx + dy*dy <= bw*bw:
                    draw.text((x + dx, y + dy), text, font=font, fill=config.BORDER_COLOR)

    # Draw main text
    draw.text((x, y), text, font=font, fill=config.TEXT_COLOR)
    img.save(output_path, "PNG")

def assemble_video(video_path, audio_path, srt_path, output_path, music_path=None):
    """
    Main composition function using MoviePy v2.x.
    """
    print("Assembling video...")
    
    # 1. Load Audio and determine duration
    voice_audio = AudioFileClip(audio_path)
    duration = voice_audio.duration
    print(f"Voice audio duration: {duration:.2f} seconds")

    # 2. Load Background Video or Image
    is_image = False
    try:
        with Image.open(video_path) as test_img:
            test_img.verify()
        is_image = True
    except Exception:
        is_image = False

    if is_image:
        print("Using background image as video...")
        # Ensure it has a correct image extension so MoviePy uses the image reader, not FFMPEG
        if not video_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_ext_path = video_path + ".jpg"
            shutil.copyfile(video_path, img_ext_path)
            original_bg_clip = ImageClip(img_ext_path)
        else:
            original_bg_clip = ImageClip(video_path)
        bg_clip = original_bg_clip.with_duration(duration)
    else:
        original_bg_clip = VideoFileClip(video_path)
        bg_clip = original_bg_clip
        
        # Loop background video if it is shorter than audio
        if bg_clip.duration < duration:
            print(f"Looping background video (duration {bg_clip.duration:.2f}s is shorter than audio)")
            bg_clip = bg_clip.with_effects([vfx.Loop(duration=duration)])
        
        # Trim to exact voice audio duration
        bg_clip = bg_clip.subclipped(0, duration)

    # 3. Resize and crop background video to target resolution (1080x1920)
    target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    clip_w, clip_h = bg_clip.size
    scale_w = target_w / clip_w
    scale_h = target_h / clip_h
    scale = max(scale_w, scale_h)
    
    bg_clip = bg_clip.resized(scale)
    new_w, new_h = bg_clip.size
    x1 = (new_w - target_w) // 2
    y1 = (new_h - target_h) // 2
    
    bg_clip = bg_clip.with_effects([vfx.Crop(x1=x1, y1=y1, width=target_w, height=target_h)])

    # 4. Generate Subtitles as ImageClips
    subtitles = parse_srt(srt_path)
    print(f"Parsed {len(subtitles)} words/subtitles.")

    # Create a temporary directory for subtitle PNGs
    temp_dir = tempfile.mkdtemp()
    sub_clips = []

    try:
        # If subtitles are already sentences (contain spaces), use them directly.
        # Otherwise (word-by-word), group them 2-by-2 to avoid flashing.
        is_word_level = all(len(s["text"].split()) <= 1 for s in subtitles)
        grouped_subs = []
        
        if not is_word_level:
            # Sentence-level: use directly
            for sub in subtitles:
                grouped_subs.append({
                    "start": sub["start"],
                    "end": sub["end"],
                    "text": sub["text"].upper()
                })
        else:
            # Word-level: group 2-by-2
            i = 0
            while i < len(subtitles):
                word1 = subtitles[i]
                if i + 1 < len(subtitles):
                    word2 = subtitles[i+1]
                    grouped_subs.append({
                        "start": word1["start"],
                        "end": word2["end"],
                        "text": f"{word1['text']} {word2['text']}".upper()
                    })
                    i += 2
                else:
                    grouped_subs.append({
                        "start": word1["start"],
                        "end": word1["end"],
                        "text": word1["text"].upper()
                    })
                    i += 1

        for idx, sub in enumerate(grouped_subs):
            # Create a PNG image for this subtitle phrase
            img_path = os.path.join(temp_dir, f"sub_{idx}.png")
            create_subtitle_image(sub["text"], img_path)
            
            # Create ImageClip for this subtitle segment
            sub_clip = (ImageClip(img_path)
                        .with_start(sub["start"])
                        .with_duration(sub["end"] - sub["start"])
                        .with_position(('center', 'center')))
            sub_clips.append(sub_clip)

        # 5. Handle Background Music (if provided)
        final_audio = voice_audio
        if music_path and os.path.exists(music_path):
            print("Adding background music...")
            original_bg_music = AudioFileClip(music_path)
            bg_music = original_bg_music
            # Loop music if needed
            if bg_music.duration < duration:
                bg_music = bg_music.with_effects([vfx.Loop(duration=duration)])
            else:
                bg_music = bg_music.subclipped(0, duration)
            # Lower background music volume
            bg_music = bg_music.with_volume_scaled(0.12)
            # Mix voice and background music
            final_audio = CompositeAudioClip([voice_audio, bg_music])

        # Set final audio to background video clip
        bg_clip = bg_clip.with_audio(final_audio)

        # 6. Composite everything together
        final_video = CompositeVideoClip([bg_clip] + sub_clips)

        # 7. Render Video to output path
        print(f"Rendering final video to {output_path}...")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="medium",
            threads=4
        )
        print("Video rendering complete!")

    finally:
        # Clean up temporary PNG files
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error removing temp files: {e}")

        # Close all clips to release file locks on Windows
        print("Closing video and audio clips...")
        if 'final_video' in locals():
            final_video.close()
        if 'bg_clip' in locals():
            bg_clip.close()
        if 'original_bg_clip' in locals():
            original_bg_clip.close()
        if 'voice_audio' in locals():
            voice_audio.close()
        if 'bg_music' in locals() and bg_music:
            bg_music.close()
        if 'original_bg_music' in locals():
            original_bg_music.close()
        if 'final_audio' in locals():
            final_audio.close()
        if 'sub_clips' in locals():
            for clip in sub_clips:
                clip.close()

if __name__ == "__main__":
    print("Run main.py to test the full pipeline.")
