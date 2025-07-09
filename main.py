import asyncio
import subprocess
import requests
import os
import urllib.request
import tarfile
from edge_tts import Communicate
from requests_toolbelt.multipart.encoder import MultipartEncoder
from market_text import generate_market_text  # ייבוא מהקוד המשני

# === הגדרות ימות המשיח ===
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
UPLOAD_URL = "https://www.call2all.co.il/ym/api/UploadFile"
TARGET_PATH = "ivr2:/2"

# === מיקום ffmpeg מקומי (לשרתים שאין להם) ===
FFMPEG_PATH = "./bin/ffmpeg"

def ensure_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        print("⬇️ מוריד ffmpeg...")
        os.makedirs("bin", exist_ok=True)
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = "bin/ffmpeg.tar.xz"
        urllib.request.urlretrieve(url, archive_path)
        with tarfile.open(archive_path) as tar:
            tar.extractall(path="bin")
        for root, dirs, files in os.walk("bin"):
            for name in files:
                if name == "ffmpeg":
                    os.rename(os.path.join(root, name), FFMPEG_PATH)
                    break

# === יצירת קובץ שמע מ־TTS והמרה ל־WAV ===
def create_wav_from_text(text, wav_filename="market.wav"):
    print("🎙️ יוצר mp3...")
    tts = Communicate(text, voice="he-IL-AvriellaNeural")
    asyncio.run(tts.save("output.mp3"))

    print("🎧 ממיר ל־WAV...")
    subprocess.run([
        FFMPEG_PATH, "-y",
        "-i", "output.mp3",
        "-ar", "8000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        wav_filename
    ])

# === העלאה לימות המשיח ===
def upload_to_yemot(wav_file):
    print("📤 מעלה לימות...")
    with open(wav_file, 'rb') as f:
        m = MultipartEncoder(
            fields={
                'token': TOKEN,
                'path': TARGET_PATH,
                'file': ('market.wav', f, 'audio/wav')
            }
        )
        r = requests.post(UPLOAD_URL, data=m, headers={'Content-Type': m.content_type})
        print("✅ תגובת ימות:", r.text)

# === הפעלת כל השלבים ===
if __name__ == "__main__":
    print("📊 מייצר טקסט תמונת שוק...")
    text = generate_market_text()
    print("📝 הטקסט:\n", text)
    ensure_ffmpeg()
    create_wav_from_text(text)
    upload_to_yemot("market.wav")
