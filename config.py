import os

# API Keys
# Gemini API Key (Set in your environment or replace with actual key string)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KOEu7p_7JRUf2avSBBru3yANnU2PqglQoV3L5TQeKvgQ")

# Pexels API Key for free stock videos (Get one free from: https://www.pexels.com/api/)
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "YOUR_PEXELS_API_KEY_HERE")

# Rotating topics for daily comedy/humor videos
TOPICS = [
    "School Viva Exams me examiner ke samne backbencher ki halat",
    "Computer Lab class me teacher ke aate hi proxy tabs close karne ki speed",
    "Ghar walo se Wi-Fi password mangne par unki badli hui shakal",
    "Backbenchers vs Toppers ke exam ke din ke ajeeb reactions",
    "College class me attendance proxy lagane ke naye tareeqe",
    "Phone ki 1 percent battery hone par mummy ki 10 missed calls ka darr",
    "Homework complete na hone par teacher ko sunaye gaye creative excuses"
]

# Audio Settings
# For Hindi (Hinglish): 'hi-IN-MadhurNeural' (Male) or 'hi-IN-SwararaNeural' (Female)
# For English: 'en-US-GuyNeural' (Male) or 'en-US-AriaNeural' (Female)
VOICE = "hi-IN-MadhurNeural"

# Video Settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
MAX_VIDEO_DURATION = 50  # maximum seconds for YouTube Short

# YouTube API Settings
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
YOUTUBE_UPLOAD_STATUS = "public"  # 'private', 'public', or 'unlisted'

# Subtitle Settings
FONT_PATH = "C:\\Windows\\Fonts\\NirmalaB.ttf"  # Nirmala UI Bold which supports Hindi/Devanagari characters on Windows
FONT_SIZE = 64
TEXT_COLOR = "yellow"
BORDER_COLOR = "black"
BORDER_WIDTH = 5
