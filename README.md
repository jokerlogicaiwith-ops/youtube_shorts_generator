# Auto YouTube Shorts Generator

Yeh ek completely automated Python script hai jo:
1. Gemini 2.0 API se ek unique daily Hinglish facts script aur video tags/titles create karta hai.
2. Microsoft Edge Neural Voice (edge-tts) se premium voiceover aur synchronized subtitles file (.vtt) generate karta hai.
3. Pexels API se topic-related portrait 9:16 background stock videos download karta hai.
4. MoviePy audio, video aur subtitles ko merge karke portrait vertical video render karta hai.
5. YouTube Data API v3 se channel par upload kar deta hai.

---

## 🛠️ Setup Instructions

### 1. API Keys & Configurations (`config.py`)
Aapko `config.py` file ko edit karke apni API keys enter karni hongi:
- **GEMINI_API_KEY**: Script generator ke liye Gemini key set karein (https://aistudio.google.com/).
- **PEXELS_API_KEY**: Stock videos search ke liye free Pexels key set karein (https://www.pexels.com/api/).
- **VOICE**: Voice accent change kar sakte hain (Default: `hi-IN-MadhurNeural`).

### 2. YouTube Upload Credentials Setup
YouTube par direct auto-upload karne ke liye:
1. Google Cloud Console (https://console.cloud.google.com/) par ek naya project banayein.
2. Search bar me **YouTube Data API v3** search karke enable karein.
3. **OAuth Consent Screen** configure karein (User Type: External, aur test users me apni email ID add karein).
4. **Credentials** tab par click karein -> **Create Credentials** -> **OAuth Client ID**.
5. Application type me **Desktop App** select karein aur name dekar save karein.
6. Banayi gayi credentials ko download karein (JSON format) aur use rename karke `client_secret.json` naam se is project folder me save kar dein.

---

## 🚀 Run & Test

1. Sabse pehle requirements install karein:
   ```cmd
   pip install -r requirements.txt
   ```
2. Manually test karne ke liye command run karein:
   ```cmd
   python main.py
   ```
3. **First-time login (OAuth)**: Pehli baar run karne par browser window open hogi. Apna YouTube account login karke allow karein. Isse ek `token.json` file generate ho jayegi jisse aage ke saare uploads bina login window ke automate ho jayenge.

---

## 📅 Daily Automation (Task Scheduler)

Is script ko rozana automatically run karne ke liye Windows Task Scheduler use karein:
1. Start Menu par search karein **Task Scheduler** aur open karein.
2. Right-side panel me **Create Basic Task...** par click karein.
3. Name rakhein `Daily YouTube Shorts`.
4. Trigger tab par **Daily** select karein aur apna preferred time (jaise subah 9:00 AM) set karein.
5. Action tab par **Start a program** select karein.
6. Program/script box me click karke browse karein aur project directory se `run_daily.bat` select karein.
7. **Start in (optional)** me project folder ka absolute path copy-paste karein:
   `C:\Users\VSRM COMPUTER CLASS\.gemini\antigravity\scratch\youtube_shorts_generator`
8. Finish karein. Ab yeh task automatic chalega aur iska history record `run_log.txt` me automatic save hota rahega!
