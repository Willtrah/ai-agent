import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")

TIMEOUT = 30

# ==============================
# OPENAI
# ==============================

def ask_openai(prompt):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-5.4-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=TIMEOUT
        )

        data = response.json()

        if response.status_code != 200:
            return f"Erreur OpenAI HTTP {response.status_code}: {str(data)[:500]}"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Erreur OpenAI: {str(e)}"


# ==============================
# CLAUDE
# ==============================

def ask_claude(prompt):
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 700,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=TIMEOUT
        )

        data = response.json()

        if response.status_code != 200:
            return f"Erreur Claude HTTP {response.status_code}: {str(data)[:500]}"

        return data["content"][0]["text"]

    except Exception as e:
        return f"Erreur Claude: {str(e)}"


# ==============================
# GEMINI
# ==============================

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
            timeout=TIMEOUT
        )

        data = response.json()

        if response.status_code != 200:
            return f"Erreur Gemini HTTP {response.status_code}: {str(data)[:500]}"

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Erreur Gemini: {str(e)}"


# ==============================
# MULTI IA
# ==============================

def nova5_compare(prompt):
    results = {
        "OPENAI": ask_openai(prompt),
        "CLAUDE": ask_claude(prompt),
        "GEMINI": ask_gemini(prompt)
    }

    response = """🤖 NOVA5 — MULTI IA

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
""".format(
        openai=results["OPENAI"],
        claude=results["CLAUDE"],
        gemini=results["GEMINI"]
    )

    return response


# ==============================
# TELEGRAM
# ==============================

def send_telegram(chat_id, text):
    if not TELEGRAM_TOKEN:
        return

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text[:4000]
        },
        timeout=60
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if not data or "message" not in data:
        return jsonify({"ok": True})

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if text.startswith("/compare"):
        question = text.replace("/compare", "", 1).strip()

        if not question:
            send_telegram(chat_id, "Utilise : /compare ta question")
            return jsonify({"ok": True})

        send_telegram(chat_id, "Nova5 analyse multi-IA...")
        response = nova5_compare(question)
        send_telegram(chat_id, response)

    else:
        send_telegram(chat_id, "Nova5 actif. Commande principale : /compare ta question")

    return jsonify({"ok": True})


# ==============================
# HEALTH
# ==============================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "openai": bool(OPENAI_API_KEY),
        "claude": bool(CLAUDE_API_KEY),
        "gemini": bool(GEMINI_API_KEY),
        "telegram": bool(TELEGRAM_TOKEN)
    })


# ==============================
# START
# ==============================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
