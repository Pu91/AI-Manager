import os
import random
import urllib.parse
import requests
from groq import Groq

# ১. GitHub Secrets থেকে গোপন Key গুলো নেওয়া হচ্ছে
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

# ২. যে ক্যাটাগরির ওপর প্রতিদিন পোস্ট হবে (ক্লায়েন্ট অনুযায়ী এটি বদলে দেবেন)
NICHE_TOPICS = [
    "Digital Marketing Tips for Small Business",
    "How AI Automation Saves Time and Money",
    "Social Media Growth Secrets",
    "Online Sales Boosting Strategies",
    "Personal Branding Tips for Entrepreneurs"
]

def generate_post_and_image_prompt():
    topic = random.choice(NICHE_TOPICS)
    
    # ক্যাপশন তৈরি করা (Groq - Llama 3.3 70B মডেল)
    caption_prompt = f"""
    You are an expert Social Media Manager. Write a highly engaging Facebook post in Bengali about: '{topic}'.
    Rules:
    1. Start with an attention-grabbing hook line.
    2. Give 3 practical and actionable bullet points.
    3. End with a question to get comments and 5 trending hashtags.
    4. Keep the tone friendly and professional. Do not put any intro text, write only the post.
    """
    
    caption_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": caption_prompt}],
        temperature=0.7
    )
    caption = caption_res.choices[0].message.content.strip()

    # ছবির জন্য ইংরেজি প্রম্পট তৈরি করা
    img_prompt_req = f"Write a short, 15-word descriptive prompt in English to generate a professional, modern 3D illustration for a social media post about: {topic}. Output ONLY the prompt."
    img_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": img_prompt_req}],
        temperature=0.7
    )
    image_prompt = img_res.choices[0].message.content.strip()
    
    return caption, image_prompt

def publish_to_facebook(caption, image_prompt):
    # Pollinations AI দিয়ে ফ্রিতে ছবি তৈরি
    encoded_prompt = urllib.parse.quote(image_prompt)
    seed = random.randint(1, 99999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&seed={seed}&nologo=true"
    
    # Facebook Graph API দিয়ে সরাসরি পেজে পোস্ট করা
    fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    payload = {
        "url": image_url,
        "caption": caption,
        "access_token": FB_ACCESS_TOKEN
    }
    
    response = requests.post(fb_url, data=payload)
    return response.json()

if __name__ == "__main__":
    print("Step 1: Generating post and image idea with Groq AI...")
    caption, image_prompt = generate_post_and_image_prompt()
    print("Generated Image Prompt:", image_prompt)
    
    print("Step 2: Publishing to Facebook Page...")
    result = publish_to_facebook(caption, image_prompt)
    print("Facebook API Response:", result)
