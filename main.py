import asyncio
import os
import subprocess
import urllib.request
import tarfile
import warnings
from edge_tts import Communicate
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
from market_text import generate_market_text  # קובץ משני שמחזיר טקסט

warnings.filterwarnings("ignore")

# === פרטי התחברות לימות המשיח ===
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
TARGET_PATH = "ivr2:/2/"  # שנה לשלוחה שברצונך להעלות אליה
FFMPEG_PATH = "./bin/ffmpeg"

# === מבטיח ש־ffmpeg מותקן ===
def ensure_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        print("⬇️ מוריד ffmpeg...")
        os.makedirs("bin", exist_ok=True)
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = "bin/ffmpeg.tar.xz"
        extract_path = "bin"
        urllib.request.urlretrieve(url, archive_path)
        with tarfile.open(archive_path) as tar:
            tar.extractall(path=extract_path)
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file == "ffmpeg":
                    os.rename(os.path.join(root, file), FFMPEG_PATH)
                    os.chmod(FFMPEG_PATH, 0o755)
                    break

# === ממיר טקסט ל־MP3 ===
async def text_to_speech(text, filename):
    communicate = Communicate(text, voice="he-IL-AvriNeural")
    await communicate.save(filename)

# === ממיר מ־MP3 ל־WAV בפורמט של ימות המשיח ===
def convert_to_wav(mp3_file, wav_file):
    ensure_ffmpeg()
    with open(os.devnull, 'w') as devnull:
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", mp3_file, "-ar", "8000", "-ac", "1", "-acodec", "pcm_s16le", wav_file],
            stdout=devnull,
            stderr=devnull
        )

# === מעלה לימות המשיח ===
def upload_to_yemot(wav_file, path):
    m = MultipartEncoder(fields={
        'token': TOKEN,
        'path': path + "001.wav",
        'file': ("001.wav", open(wav_file, 'rb'), 'audio/wav')
    })
    r = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=m, headers={'Content-Type': m.content_type})
    if r.ok:
        print("✅ הועלה בהצלחה")
    else:
        print("❌ שגיאה בהעלאה:", r.text)

# === פונקציית הרצה ראשית ===
async def main():
    print("📊 מייצר טקסט תמונת שוק...")
    text = generate_market_text()
    if not text:
        print("⚠️ לא נוצר טקסט")
        return

    print("📝 הטקסט:\n", text)
    await text_to_speech(text, "market.mp3")
    convert_to_wav("market.mp3", "market.wav")
    upload_to_yemot("market.wav", TARGET_PATH)

if __name__ == "__main__":
    asyncio.run(main())
