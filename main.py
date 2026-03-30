import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ===============================
# VARIABLES
# ===============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

RAILWAY_URL = "https://ai-agent-production-9fff.up.railway.app"

# ===============================
# HOME
# ===============================

@app.route("/", methods=["GET"])
def home():
    return "Nova5 AI Server Running"

# ===============================
# HEALTH
# ===============================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "bot": "Nova5",
        "railway": "connected",
        "telegram_token_loaded": bool(TELEGRAM_TOKEN),
        "openai_loaded": bool(OPENAI_API_KEY),
        "anthropic_loaded": bool(ANTHROPIC_API_KEY),
        "gemini_loaded": bool(GEMINI_API_KEY)
    })

# ===============================
# TELEGRAM SEND
# ===============================

def send_telegram(chat_id, text):
    if not TELEGRAM_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text[:4000]
        },
        timeout=60
    )

# ===============================
# OPENAI
# ===============================

def ask_openai(prompt):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4.1-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )

        result = response.json()

        if response.status_code != 200:
            return f"Erreur OpenAI HTTP {response.status_code}: {str(result)[:500]}"

        if "choices" not in result:
            return f"Erreur OpenAI format: {str(result)[:500]}"

        return result["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Erreur OpenAI : {str(e)}"

# ===============================
# CLAUDE
# ===============================

def ask_claude(prompt):
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )

        result = response.json()

        if response.status_code != 200:
            return f"Erreur Claude HTTP {response.status_code}: {str(result)[:500]}"

        if "content" not in result:
            return f"Erreur Claude format: {str(result)[:500]}"

        return result["content"][0]["text"]

    except Exception as e:
        return f"Erreur Claude : {str(e)}"

# ===============================
# GEMINI
# ===============================

def ask_gemini(prompt):
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=60
        )

        result = response.json()

        if response.status_code != 200:
            return f"Erreur Gemini HTTP {response.status_code}: {str(result)[:500]}"

        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Erreur Gemini : {str(e)}"

# ===============================
# MULTI IA
# ===============================

def multi_ai(prompt):
    openai = ask_openai(prompt)
    claude = ask_claude(prompt)
    gemini = ask_gemini(prompt)

    return f"""🤖 NOVA5 — MULTI IA

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
"""

# ===============================
# WEBHOOK TELEGRAM
# ===============================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if not data or "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if text.startswith("/compare"):
        prompt = text.replace("/compare", "", 1).strip()

        if not prompt:
            send_telegram(chat_id, "Utilise : /compare ta question")
            return "ok"

        send_telegram(chat_id, "Nova5 analyse multi-IA...")
        result = multi_ai(prompt)
        send_telegram(chat_id, result)

    elif text == "/start":
        send_telegram(chat_id, "Nova5 actif. Commande principale : /compare ta question")

    else:
        send_telegram(chat_id, "Nova5 actif. Utilise /compare ta question")

    return "ok"

# ===============================
# SET WEBHOOK
# ===============================

@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({
            "ok": False,
            "error": "TELEGRAM token missing in environment"
        }), 500

    webhook_url = f"{RAILWAY_URL}/webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"

    r = requests.get(url, timeout=60)
    return r.text, r.status_code, {"Content-Type": "application/json"}

# ===============================
# DELETE WEBHOOK
# ===============================

@app.route("/deletewebhook", methods=["GET"])
def delete_webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({
            "ok": False,
            "error": "TELEGRAM token missing in environment"
        }), 500

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
    r = requests.get(url, timeout=60)
    return r.text, r.status_code, {"Content-Type": "application/json"}

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
