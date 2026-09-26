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

@app.route("/")
def home():
    return "Instagram AI Agent is Running!"

@app.route("/auto-post", methods=["GET"])
def auto_post():
    if request.args.get("pin") != SECRET_PIN:
        return jsonify({"error": "Wrong PIN!"}), 403

    try:
        # ১. আগে চেক করা হচ্ছে সব Key ঠিকমতো দেওয়া আছে কি না
        if not GROQ_API_KEY or not IG_USERNAME or not IG_PASSWORD:
            return jsonify({
                "error": "Environment Variables Missing!",
                "GROQ_API_KEY_SET": bool(GROQ_API_KEY),
                "IG_USERNAME_SET": bool(IG_USERNAME),
                "IG_PASSWORD_SET": bool(IG_PASSWORD)
            }), 400

        groq_client = Groq(api_key=GROQ_API_KEY)
        topic = "Digital Marketing Tips for Small Business"

        # ২. Groq দিয়ে ক্যাপশন তৈরি
        caption_res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Write an engaging Instagram post in Bengali about '{topic}' with 3 bullet points and 5 hashtags. Output ONLY the post."}]
        )
        caption = caption_res.choices[0].message.content.strip()

        # ৩. ছবি ডাউনলোড
        image_url = f"https://image.pollinations.ai/prompt/modern%203d%20digital%20marketing%20illustration?width=1080&height=1080&seed={random.randint(1,9999)}&nologo=true"
        img_data = requests.get(image_url, timeout=30).content
        with open("post.jpg", "wb") as f:
            f.write(img_data)

        # ৪. Instagram লগইন ও পোস্ট
        cl = Client()
        cl.login(IG_USERNAME, IG_PASSWORD)
        media = cl.photo_upload("post.jpg", caption)

        return jsonify({"status": "Posted to Instagram!", "media_id": str(media.pk)})

    except Exception as e:
        # কোনো ভুল হলে সেটি স্ক্রিনে পরিষ্কারভাবে দেখাবে
        return jsonify({
            "status": "Error Occurred",
            "exact_error": str(e)
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
