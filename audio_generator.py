import asyncio
import os
import sys
import edge_tts
import config

def generate_audio_and_subtitles(text, audio_path, subtitle_path):
    """
    Converts text to speech and generates synchronized subtitles (.vtt).
    """
    print(f"Generating TTS audio using voice '{config.VOICE}'...")
    
    # edge-tts is asynchronous, so we wrap it in an event loop
    async def _generate():
        communicate = edge_tts.Communicate(text, config.VOICE)
        submaker = edge_tts.SubMaker()
        
        with open(audio_path, "wb") as fp:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    fp.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    submaker.feed(chunk)
                    
        # Write SRT subtitles file
        with open(subtitle_path, "w", encoding="utf-8") as f:
            # get_srt() generates SRT style subtitles
            f.write(submaker.get_srt())
            
    try:
        # Run async function
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(_generate())
        print(f"Saved audio to: {audio_path}")
        print(f"Saved subtitles to: {subtitle_path}")
        return True
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False

if __name__ == "__main__":
    # Test TTS generation locally
    test_text = "Dosto, kya aapko pata hai ki hamara dimaag kitna powerful hai? Chaliye aaj jaante hain!"
    audio_out = "test_voice.mp3"
    sub_out = "test_subs.srt"
    
    generate_audio_and_subtitles(test_text, audio_out, sub_out)
    
    # Cleanup test files if they exist
    if os.path.exists(audio_out):
        os.remove(audio_out)
    if os.path.exists(sub_out):
        os.remove(sub_out)
