import os
import time
import logging
import threading

from flask import Flask, request

import requests

# ================================
# Configuration
# ================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

print("AI Multi-Agent System Started")


# ================================
# OpenAI
# ================================

def ask_openai(prompt):

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
    result = response.json()

    return result["choices"][0]["message"]["content"]


# ================================
# Claude
# ================================

def ask_claude(prompt):

    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["content"][0]["text"]


# ================================
# Gemini
# ================================

def ask_gemini(prompt):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

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
    result = response.json()

    return result["candidates"][0]["content"]["parts"][0]["text"]


# ================================
# Multi IA réel
# ================================

def ask_all_models(prompt):

    responses = {}

    try:
        start = time.time()
        responses["openai"] = ask_openai(prompt)
        responses["openai_time"] = round(time.time() - start, 2)
    except Exception as e:
        responses["openai"] = f"Erreur OpenAI : {e}"

    try:
        start = time.time()
        responses["claude"] = ask_claude(prompt)
        responses["claude_time"] = round(time.time() - start, 2)
    except Exception as e:
        responses["claude"] = f"Erreur Claude : {e}"

    try:
        start = time.time()
        responses["gemini"] = ask_gemini(prompt)
        responses["gemini_time"] = round(time.time() - start, 2)
    except Exception as e:
        responses["gemini"] = f"Erreur Gemini : {e}"

    return responses


# ================================
# Compare
# ================================

def compare_models(prompt):

    results = ask_all_models(prompt)

    return f"""

🤖 NOVA5 — MULTI IA

---------------------

🧠 OPENAI ({results.get('openai_time','?')}s)

{results['openai']}

---------------------

🧠 CLAUDE ({results.get('claude_time','?')}s)

{results['claude']}

---------------------

🧠 GEMINI ({results.get('gemini_time','?')}s)

{results['gemini']}

"""


# ================================
# Telegram
# ================================

def send_telegram(chat_id, text):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text[:4000]
    }

    requests.post(url, data=data)


@app.route("/", methods=["POST"])
def telegram_webhook():

    data = request.json

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not text:
        return "ok"

    if text.startswith("/compare"):

        question = text.replace("/compare", "").strip()

        send_telegram(chat_id, "Nova5 analyse multi-IA...")

        response = compare_models(question)

        send_telegram(chat_id, response)

    else:

        send_telegram(chat_id, "Nova5 actif. Utilise /compare question")

    return "ok"


# ================================
# Heartbeat
# ================================

def heartbeat():

    while True:
        logging.info("Heartbeat OK")
        time.sleep(60)


threading.Thread(target=heartbeat, daemon=True).start()
