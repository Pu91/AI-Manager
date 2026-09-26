import os
import random
import urllib.parse
import requests
from flask import Flask, request, jsonify
from groq import Groq
from instagrapi import Client

app = Flask(__name__)

# শুধু এই ৪টি জিনিস Render-এ দেবেন (কোনো Token লাগবে না)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")
SECRET_PIN = os.environ.get("SECRET_PIN", "1234")

groq_client = Groq(api_key=GROQ_API_KEY)

NICHE_TOPICS = [
    "Digital Marketing Tips for Small Business",
    "How AI Automation Saves Time and Money",
    "Social Media Growth Secrets",
    "Online Sales Boosting Strategies"
]

@app.route("/")
def home():
    return "Instagram AI Agent is Running!"

@app.route("/auto-post", methods=["GET"])
def auto_post():
    if request.args.get("pin") != SECRET_PIN:
        return jsonify({"error": "Wrong PIN!"}), 403

    topic = random.choice(NICHE_TOPICS)

    # ১. Groq দিয়ে বাংলা ক্যাপশন তৈরি
    caption_res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"Write an engaging Instagram post in Bengali about '{topic}' with 3 bullet points and 5 hashtags. Output ONLY the post."}]
    )
    caption = caption_res.choices[0].message.content.strip()

    # ২. AI দিয়ে ছবি তৈরি ও ডাউনলোড
    img_res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"Write a 10-word English image prompt for a 3D illustration about: {topic}. Output ONLY the prompt."}]
    )
    image_prompt = urllib.parse.quote(img_res.choices[0].message.content.strip())
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1080&height=1080&seed={random.randint(1,9999)}&nologo=true"

    img_data = requests.get(image_url).content
    with open("post.jpg", "wb") as f:
        f.write(img_data)

    # ৩. সরাসরি Username ও Password দিয়ে Instagram-এ পোস্ট
    cl = Client()
    cl.login(IG_USERNAME, IG_PASSWORD)
    media = cl.photo_upload("post.jpg", caption)

    return jsonify({"status": "Posted to Instagram!", "media_id": str(media.pk)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
