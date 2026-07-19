import json
import os
import sys
import config

def generate_script(topic):
    prompt = f"""
    Create a highly engaging, funny, and relatable comedy script/joke for a YouTube Short (vertical video) about the topic: "{topic}".
    The channel is '@jokerlogicaiwith', which makes clean, family-friendly Hindi comedy/humor shorts about student life, college life, and daily relatable situations.
    The script must be written in conversational Hinglish (Hindi using the English/Latin alphabet, the way students chat with each other, e.g., 'Yaar jab viva chal raha ho...').
    Keep the tone funny, sarcastic, and lighthearted. Keep it concise (around 40-60 words) so it fits in a 15-25 second video.

    Return your output strictly in JSON format. Do not wrap the JSON in markdown code blocks. The JSON must contain:
    1. "title": A catchy, funny video title.
    2. "description": A video description with relevant comedy hashtags like #shorts #comedy #jokes #relatable #studentlife #jokerlogic.
    3. "pexels_query": A simple English search term to find a funny or expressive background video (e.g., "funny baby laughing", "confused student writing", "running fast classroom", "shocked face expression").
    4. "script_paragraphs": A list of 3-4 short sentences/statements to be read sequentially.
    """

    print(f"Generating script for topic: '{topic}' using Gemini API...")

    # Method 1: Try new google-genai SDK (recommended for Gemini 2.0/2.5)
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text.strip())
    except ImportError:
        print("google-genai SDK not found, trying legacy google-generativeai...")
    except Exception as e:
        print(f"Error with google-genai: {e}. Trying legacy SDK...")

    # Method 2: Try legacy google-generativeai SDK
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"Error with legacy google-generativeai: {e}")
        # If both fail, let the user know
        raise RuntimeError("Failed to connect to Gemini API. Please check your GEMINI_API_KEY or package installation.")

if __name__ == "__main__":
    # Test script generation locally
    # Set a dummy API key for testing compilation if none is present
    if config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("Please set your GEMINI_API_KEY in config.py or environment before running.")
        sys.exit(1)
        
    test_topic = config.TOPICS[0]
    try:
        result = generate_script(test_topic)
        print("Generated Output Successfully:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Test run failed: {e}")
