import os
import requests
import time
from flask import Flask, request

app = Flask(__name__)

# ================================
# VARIABLES
# ================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

RAILWAY_URL = "https://ai-agent-production-9fff.up.railway.app"


# ================================
# TELEGRAM SEND
# ================================

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, json=data)


# ================================
# OPENAI
# ================================

def ask_openai(prompt):
    try:
        start = time.time()

        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data)

        elapsed = round(time.time() - start, 2)

        result = response.json()

        return f"{result['choices'][0]['message']['content']} ({elapsed}s)"

    except Exception as e:
        return f"Erreur OpenAI : {str(e)}"


# ================================
# CLAUDE
# ================================

def ask_claude(prompt):
    try:
        start = time.time()

        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data)

        elapsed = round(time.time() - start, 2)

        result = response.json()

        return f"{result['content'][0]['text']} ({elapsed}s)"

    except Exception as e:
        return f"Erreur Claude : {str(e)}"


# ================================
# GEMINI
# ================================

def ask_gemini(prompt):
    try:
        start = time.time()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)

        elapsed = round(time.time() - start, 2)

        result = response.json()

        text = result["candidates"][0]["content"]["parts"][0]["text"]

        return f"{text} ({elapsed}s)"

    except Exception as e:
        return f"Erreur Gemini : {str(e)}"


# ================================
# MULTI IA
# ================================

def multi_ai(prompt):

    openai = ask_openai(prompt)
    claude = ask_claude(prompt)
    gemini = ask_gemini(prompt)

    return f"""
🤖 NOVA5 — MULTI IA

---------------------

🧠 OPENAI
{openai}

---------------------

🧠 CLAUDE
{claude}

---------------------

🧠 GEMINI
{gemini}

---------------------

Nova5 actif
"""


# ================================
# AUTO WEBHOOK
# ================================

@app.route("/setwebhook")
def set_webhook():

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={RAILWAY_URL}"

    r = requests.get(url)

    return r.text


# ================================
# WEBHOOK TELEGRAM
# ================================

@app.route("/", methods=["POST"])
def webhook():

    data = request.json

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/compare"):

            prompt = text.replace("/compare", "").strip()

            send_message(chat_id, "Nova5 analyse multi-IA...")

            result = multi_ai(prompt)

            send_message(chat_id, result)

        else:

            send_message(chat_id, "Nova5 actif. Utilise /compare")

    return "ok"


# ================================
# HEALTH
# ================================

@app.route("/", methods=["GET"])
def home():
    return "Nova5 Online"


# ================================
# RUN
# ================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
