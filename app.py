import os
import random
import urllib.parse
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Render-এর Environment Variables থেকে Key নেওয়া হবে
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
SECRET_PIN = os.environ.get("SECRET_PIN", "1234") # যাতে অন্য কেউ আপনার পোস্ট ট্রিগার না করতে পারে

client = Groq(api_key=GROQ_API_KEY)

NICHE_TOPICS = [
    "Digital Marketing Tips for Small Business",
    "How AI Automation Saves Time and Money",
    "Social Media Growth Secrets",
    "Online Sales Boosting Strategies"
]

@app.route("/")
def home():
    return "AI Social Media Manager Agent is Running Live on Render!"

# ১. অটোমেটিক ফেসবুক পোস্ট করার রাউট
@app.route("/auto-post", methods=["GET"])
def auto_post():
    # সিকিউরিটি চেক
    pin = request.args.get("pin")
    if pin != SECRET_PIN:
        return jsonify({"error": "Unauthorized! Wrong PIN."}), 403

    topic = random.choice(NICHE_TOPICS)

    # Groq দিয়ে বাংলা ক্যাপশন তৈরি
    caption_prompt = f"Write an engaging Facebook post in Bengali about '{topic}' with a hook, 3 bullet points, and 5 hashtags. Output only the post text."
    caption_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": caption_prompt}]
    )
    caption = caption_res.choices[0].message.content.strip()

    # ছবির প্রম্পট ও URL তৈরি
    img_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"Write a 12-word English image prompt for a modern 3D illustration about: {topic}. Output ONLY the prompt."}]
    )
    image_prompt = img_res.choices[0].message.content.strip()
    encoded_prompt = urllib.parse.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&seed={random.randint(1,9999)}&nologo=true"

    # ফেসবুক পেজে পোস্ট করা
    fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    payload = {
        "url": image_url,
        "caption": caption,
        "access_token": FB_ACCESS_TOKEN
    }
    fb_response = requests.post(fb_url, data=payload).json()

    return jsonify({
        "status": "Success",
        "topic": topic,
        "facebook_response": fb_response
    })

# ২. কাস্টমারদের মেসেজ/কমেন্টের রিপ্লাই দেওয়ার রাউট
@app.route("/ask-agent", methods=["POST"])
def ask_agent():
    data = request.json
    user_message = data.get("message", "")
    
    reply_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful customer support agent for a Digital Marketing Agency. Reply politely in Bengali in 2 short sentences."},
            {"role": "user", "content": user_message}
        ]
    )
    return jsonify({"reply": reply_res.choices[0].message.content.strip()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
