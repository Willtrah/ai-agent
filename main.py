import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")

# ===============================
# HOME
# ===============================

@app.route("/")
def home():
    return "Nova5 AI Server Running"

# ===============================
# HEALTH CHECK
# ===============================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "bot": "Nova5",
        "railway": "connected"
    })

# ===============================
# TELEGRAM WEBHOOK
# ===============================

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text.startswith("/compare"):

        reply = "🤖 Nova5 analyse multi-IA...\n\n"

        # OpenAI
        try:
            openai_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": "gpt-4.1-mini",
                    "messages": [
                        {"role": "user", "content": text.replace("/compare", "")}
                    ]
                }
            )

            openai_result = openai_response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            openai_result = f"Erreur OpenAI : {str(e)}"

        reply += f"🧠 OPENAI\n{openai_result}\n\n"

        send_telegram(chat_id, reply)

    return "ok"


# ===============================
# SEND TELEGRAM
# ===============================

def send_telegram(chat_id, text):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


# ===============================
# SET WEBHOOK
# ===============================

@app.route("/setwebhook")
def set_webhook():

    webhook_url = f"https://{RAILWAY_URL}/webhook"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"

    r = requests.get(url)

    return r.text


# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
