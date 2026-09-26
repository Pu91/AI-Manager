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

def generate_with_groq(client, prompt, max_tok=300):
    models = client.models.list().data
    # সব চালু টেক্সট মডেল খুঁজে বের করা
    candidate_models = [
        m.id for m in models
        if any(k in m.id.lower() for k in ["llama", "gemma", "mixtral", "qwen"])
        and not any(s in m.id.lower() for s in ["guard", "whisper", "tts", "audio", "embed", "vision"])
    ]
    
    last_err = None
    for model_id in candidate_models:
        try:
            res = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tok,
                temperature=0.7
            )
            return res.choices[0].message.content.strip(), model_id
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"All models failed. Last error: {last_err}")

@app.route("/")
def home():
    return "Instagram AI Agent is Running!"

@app.route("/auto-post", methods=["GET"])
def auto_post():
    if request.args.get("pin") != SECRET_PIN:
        return jsonify({"error": "Wrong PIN!"}), 403

    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        topic = random.choice(NICHE_TOPICS)

        # ১. ক্যাপশন তৈরি (মাত্র ৩০০ টোকেনের মধ্যে)
        caption_prompt = f"Write an engaging Instagram post in Bengali about '{topic}' with 3 short bullet points and 5 hashtags. Output ONLY the post."
        caption, used_model = generate_with_groq(groq_client, caption_prompt, max_tok=300)

        # ২. ছবির লিংক তৈরি
        image_prompt = urllib.parse.quote(f"modern 3d illustration of {topic}, vibrant colors, minimal")
        image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1080&height=1080&seed={random.randint(1,99999)}&nologo=true"

        # ৩. Webhook থাকলে সেখানে পাঠানো
        webhook_status = "Not connected yet"
        if MAKE_WEBHOOK_URL:
            requests.post(MAKE_WEBHOOK_URL, json={"caption": caption, "image_url": image_url})
            webhook_status = "Sent to Instagram Webhook Successfully!"

        return f"""
        <html>
        <body style="font-family: sans-serif; padding: 20px; max-width: 500px; margin: auto;">
            <h2 style="color: green;">AI Post Generated Successfully!</h2>
            <p><b>Model Used:</b> {used_model}</p>
            <p><b>Webhook Status:</b> {webhook_status}</p>
            <img src="{image_url}" style="width: 100%; border-radius: 10px;" />
            <h3>Generated Bengali Caption:</h3>
            <div style="background: #f4f4f4; padding: 15px; border-radius: 8px; white-space: pre-wrap;">{caption}</div>
        </body>
        </html>
        """

    except Exception as e:
        return jsonify({"status": "Error Occurred", "exact_error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
