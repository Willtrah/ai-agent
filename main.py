import os
import requests
import time
from flask import Flask, request

app = Flask(__name__)

# ================================
# API KEYS
# ================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ================================
# TELEGRAM SEND MESSAGE
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

        response = requests.post(url, headers=headers, json=data, timeout=60)

        elapsed = round(time.time() - start, 2)

        if response.status_code != 200:
            return f"Erreur OpenAI HTTP ({elapsed}s): {response.text[:300]}"

        result = response.json()

        if "choices" not in result:
            return f"Erreur OpenAI format ({elapsed}s): {str(result)[:300]}"

        return f"{result['choices'][0]['message']['content']}\n({elapsed}s)"

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
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)

        elapsed = round(time.time() - start, 2)

        if response.status_code != 200:
            return f"Erreur Claude HTTP ({elapsed}s): {response.text[:300]}"

        result = response.json()

        if "content" not in result:
            return f"Erreur Claude format ({elapsed}s): {str(result)[:300]}"

        return f"{result['content'][0]['text']}\n({elapsed}s)"

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

        response = requests.post(url, headers=headers, json=data, timeout=60)

        elapsed = round(time.time() - start, 2)

        if response.status_code != 200:
            return f"Erreur Gemini HTTP ({elapsed}s): {response.text[:300]}"

        result = response.json()

        text = result["candidates"][0]["content"]["parts"][0]["text"]

        return f"{text}\n({elapsed}s)"

    except Exception as e:
        return f"Erreur Gemini : {str(e)}"


# ================================
# NOVA5 MULTI IA
# ================================

def multi_ai(prompt):

    openai = ask_openai(prompt)
    claude = ask_claude(prompt)
    gemini = ask_gemini(prompt)

    response = f"""
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

Nova5 actif.
Utilise /compare question
"""

    return response


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

            send_message(chat_id, "Nova5 actif. Utilise /compare question")

    return "ok"


# ================================
# HEALTH CHECK
# ================================

@app.route("/", methods=["GET"])
def home():
    return "Nova5 Online"


# ================================
# RUN
# ================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
