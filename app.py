import os
import random
import urllib.parse
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL", "")
SECRET_PIN = os.environ.get("SECRET_PIN", "123456789")

NICHE_TOPICS = [
    "Digital Marketing Tips for Small Business",
    "How AI Automation Saves Time and Money",
    "Social Media Growth Secrets",
    "Online Sales Boosting Strategies"
]

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
        topic = random.choice(NICHE_TOPICS)

        # ১. Groq AI দিয়ে বাংলা ক্যাপশন তৈরি
        caption_res = groq_client.chat.completions.create(
            model=active_model,
            messages=[{"role": "user", "content": f"Write an engaging Instagram post in Bengali about '{topic}' with 3 bullet points and 5 hashtags. Output ONLY the post."}]
        )
        caption = caption_res.choices[0].message.content.strip()

        # ২. AI দিয়ে ছবির লিংক তৈরি
        img_res = groq_client.chat.completions.create(
            model=active_model,
            messages=[{"role": "user", "content": f"Write a 10-word English image prompt for a modern 3D illustration about: {topic}. Output ONLY the prompt."}]
        )
        image_prompt = urllib.parse.quote(img_res.choices[0].message.content.strip())
        image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1080&height=1080&seed={random.randint(1,99999)}&nologo=true"

        # ৩. Make.com Webhook দেওয়া থাকলে সরাসরি Instagram/Facebook-এ পোস্ট করবে
        webhook_status = "Not connected yet"
        if MAKE_WEBHOOK_URL:
             requests.post(MAKE_WEBHOOK_URL, json={"caption": caption, "image_url": image_url})
            webhook_status = "Sent to Instagram Webhook Successfully!"

        # স্ক্রিনে সুন্দরভাবে ছবি ও ক্যাপশন দেখানো
        return f"""
        <html>
        <body style="font-family: sans-serif; padding: 20px; max-width: 500px; margin: auto;">
            <h2 style="color: green;">✅ AI Post Generated Successfully!</h2>
            <p><b>Webhook Status:</b> {webhook_status}</p>
            <img src="{image_url}" style="width: 100%; border-radius: 10px;" />
            <h3>Generated Caption:</h3>
            <div style="background: #f4f4f4; padding: 15px; border-radius: 8px; white-space: pre-wrap;">{caption}</div>
        </body>
        </html>
        """

    except Exception as e:
        return jsonify({"status": "Error Occurred", "exact_error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
