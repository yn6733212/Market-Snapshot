import os
import datetime
import requests
import subprocess
import urllib.request
import tarfile
import warnings
from edge_tts import Communicate
from requests_toolbelt.multipart.encoder import MultipartEncoder
from market_text import generate_market_text  # ייבוא מהקובץ המשני

warnings.filterwarnings("ignore")

# === פרטי התחברות לימות המשיח ===
USERNAME = "0733181201"
PASSWORD = "6714453"
YEMOT_TOKEN = f"{USERNAME}:{PASSWORD}"
UPLOAD_URL = "https://www.call2all.co.il/ym/api/UploadFile"
TARGET_PATH = "ivr2:/2"  # שלוחה 2

# === קבצים ושמות ===
MP3_FILE = "output.mp3"
WAV_FILE = "output.wav"
FFMPEG_PATH = "./bin/ffmpeg"

# === הורדת ffmpeg אם לא קיים ===
def ensure_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        print("⬇️ מוריד ffmpeg...")
        os.makedirs("bin", exist_ok=True)
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = "bin/ffmpeg.tar.xz"
        urllib.request.urlretrieve(url, archive_path)
        with tarfile.open(archive_path) as tar:
            tar.extractall(path="bin")
        # איתור הקובץ בפנים
        for root, dirs, files in os.walk("bin"):
            for file in files:
                if file == "ffmpeg":
                    os.rename(os.path.join(root, file), FFMPEG_PATH)
        os.chmod(FFMPEG_PATH, 0o755)

# === יצירת קובץ MP3 מהטקסט ===
def create_mp3(text):
    print("🎙️ יוצר MP3 מהטקסט...")
    tts = Communicate(text=text, voice="he-IL-AvriNeural")
    try:
        import asyncio
        asyncio.run(tts.save(MP3_FILE))
    except Exception as e:
        print(f"❌ שגיאה ביצירת MP3: {e}")
        exit()

# === המרת MP3 ל־WAV תקני לימות המשיח ===
def convert_to_wav():
    print("🎛️ ממיר ל־WAV...")
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", MP3_FILE,
        "-ar", "8000", "-ac", "1", "-acodec", "pcm_s16le", WAV_FILE
    ])

# === העלאת WAV לימות המשיח ===
def upload_to_yemot():
    print("⏫ מעלה לימות המשיח...")
    with open(WAV_FILE, "rb") as f:
        m = MultipartEncoder(fields={
            "token": YEMOT_TOKEN,
            "path": TARGET_PATH,
            "message": (WAV_FILE, f, "audio/wav")
        })
        response = requests.post(UPLOAD_URL, data=m, headers={"Content-Type": m.content_type})
        if "ok" in response.text:
            print("✅ הועלה בהצלחה!")
        else:
            print(f"❌ שגיאה בהעלאה: {response.text}")

# === הרצה ===
if __name__ == "__main__":
    print("📊 מייצר טקסט תמונת שוק...")
    try:
        text = generate_market_text()
        print("📝 הטקסט:\n", text)
    except Exception as e:
        print(f"❌ שגיאה בהפקת טקסט: {e}")
        exit()

    ensure_ffmpeg()
    create_mp3(text)
    convert_to_wav()
    upload_to_yemot()
