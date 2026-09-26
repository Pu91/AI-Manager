import os
import random
import urllib.parse
import requests
from flask import Flask, request, jsonify
from groq import Groq
from instagrapi import Client

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")
IG_SESSION_ID = os.environ.get("IG_SESSION_ID", "")
SECRET_PIN = os.environ.get("SECRET_PIN", "123456789")

def get_working_groq_model(client):
    models = client.models.list().data
    for m in models:
        lower_id = m.id.lower()
        if any(name in lower_id for name in ["llama", "qwen", "gemma", "mixtral"]) and not any(skip in lower_id for skip in ["guard", "whisper", "tts", "audio", "embed"]):
            return m.id
    return models[0].id

@app.route("/")
def home():
    return "Instagram AI Agent is Running!"

@app.route("/auto-post", methods=["GET"])
def auto_post():
    if request.args.get("pin") != SECRET_PIN:
        return jsonify({"error": "Wrong PIN!"}), 403

    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        active_model = get_working_groq_model(groq_client)
        topic = "Digital Marketing Tips for Small Business"

        # ১. Groq দিয়ে বাংলা ক্যাপশন তৈরি
        caption_res = groq_client.chat.completions.create(
            model=active_model,
            messages=[{"role": "user", "content": f"Write an engaging Instagram post in Bengali about '{topic}' with 3 bullet points and 5 hashtags. Output ONLY the post."}]
        )
        caption = caption_res.choices[0].message.content.strip()

        # ২. ছবি ডাউনলোড
        image_url = f"https://image.pollinations.ai/prompt/modern%203d%20digital%20marketing%20illustration?width=1080&height=1080&seed={random.randint(1,9999)}&nologo=true"
        img_data = requests.get(image_url, timeout=30).content
        with open("post.jpg", "wb") as f:
            f.write(img_data)

        # ৩. নতুন ভার্সন + bloks_versioning_id একসাথে সেট করে লগইন
        cl = Client()
        bloks_id = cl.device_settings.get(
            "bloks_versioning_id",
            "ce555821069428c2549e262922a720c280c638c7f81e06f6999c7224d8c0f082"
        )
        cl.set_device({
            "app_version": "365.0.0.35.96",
            "android_version": 34,
            "android_release": "14.0",
            "dpi": "480dpi",
            "resolution": "1080x2400",
            "manufacturer": "Google",
            "device": "husky",
            "model": "Pixel 8 Pro",
            "cpu": "tensor",
            "version_code": "671234567",
            "bloks_versioning_id": bloks_id
        })
        cl.set_user_agent(
            "Instagram 365.0.0.35.96 Android (34/14.0; 480dpi; 1080x2400; Google; Pixel 8 Pro; husky; tensor; en_IN; 671234567)"
        )
        cl.set_locale("en_IN")
        cl.set_timezone_offset(19800)

        if IG_SESSION_ID:
            cl.login_by_sessionid(IG_SESSION_ID)
        else:
            cl.login(IG_USERNAME, IG_PASSWORD)

        media = cl.photo_upload("post.jpg", caption)

        return jsonify({
            "status": "Success! Posted to Instagram!",
            "used_model": active_model,
            "media_id": str(media.pk)
        })

    except Exception as e:
        return jsonify({
            "status": "Error Occurred",
            "exact_error": str(e)
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
