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
SECRET_PIN = os.environ.get("SECRET_PIN", "123456789")

def get_working_groq_model(client):
    # Groq-e bortomane je model-gulo chalu ache segulo khuje ber kora
    models = client.models.list().data
    available_ids = [m.id for m in models]
    
    # Pochonder text model khuje neya
    for m_id in available_ids:
        lower_id = m_id.lower()
        if any(name in lower_id for name in ["llama", "qwen", "gemma", "mixtral", "deepseek"]) and not any(skip in lower_id for skip in ["guard", "whisper", "tts", "audio", "embed"]):
            return m_id
    return available_ids[0]

@app.route("/")
def home():
    return "Instagram AI Agent is Running!"

@app.route("/auto-post", methods=["GET"])
def auto_post():
    if request.args.get("pin") != SECRET_PIN:
        return jsonify({"error": "Wrong PIN!"}), 403

    try:
        if not GROQ_API_KEY or not IG_USERNAME or not IG_PASSWORD:
            return jsonify({
                "error": "Environment Variables Missing!",
                "GROQ_API_KEY_SET": bool(GROQ_API_KEY),
                "IG_USERNAME_SET": bool(IG_USERNAME),
                "IG_PASSWORD_SET": bool(IG_PASSWORD)
            }), 400

        groq_client = Groq(api_key=GROQ_API_KEY)
        active_model = get_working_groq_model(groq_client)
        topic = "Digital Marketing Tips for Small Business"

        # 1. Groq diye Bangla caption toiri
        caption_res = groq_client.chat.completions.create(
            model=active_model,
            messages=[{"role": "user", "content": f"Write an engaging Instagram post in Bengali about '{topic}' with 3 bullet points and 5 hashtags. Output ONLY the post."}]
        )
        caption = caption_res.choices[0].message.content.strip()

        # 2. Chobi download
        image_url = f"https://image.pollinations.ai/prompt/modern%203d%20digital%20marketing%20illustration?width=1080&height=1080&seed={random.randint(1,9999)}&nologo=true"
        img_data = requests.get(image_url, timeout=30).content
        with open("post.jpg", "wb") as f:
            f.write(img_data)

        # 3. Instagram login o post
        cl = Client()
        cl.login(IG_USERNAME, IG_PASSWORD)
        media = cl.photo_upload("post.jpg", caption)

        return jsonify({
            "status": "Posted to Instagram!",
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
