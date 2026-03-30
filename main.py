import os import requests from flask import Flask, request, jsonify

app = Flask(name)

==============================

CONFIG

==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY") GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" TIMEOUT = 10

==============================

OPENAI

==============================

def ask_openai(prompt): try: response = requests.post( "https://api.openai.com/v1/chat/completions", headers={ "Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json" }, json={ "model": "gpt-4o-mini", "messages": [ {"role": "user", "content": prompt} ] }, timeout=TIMEOUT )

data = response.json()
    return data["choices"][0]["message"]["content"]

except Exception as e:
    return f"Erreur OpenAI: {str(e)}"

==============================

CLAUDE

==============================

def ask_claude(prompt): try: response = requests.post( "https://api.anthropic.com/v1/messages", headers={ "x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" }, json={ "model": "claude-3-haiku-20240307", "max_tokens": 500, "messages": [ { "role": "user", "content": prompt } ] }, timeout=TIMEOUT )

data = response.json()
    return data["content"][0]["text"]

except Exception as e:
    return f"Erreur Claude: {str(e)}"

==============================

GEMINI

==============================

def ask_gemini(prompt): try: response = requests.post( f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}", headers={ "Content-Type": "application/json" }, json={ "contents": [{ "parts": [{"text": prompt}] }] }, timeout=TIMEOUT )

data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

except Exception as e:
    return f"Erreur Gemini: {str(e)}"

==============================

MULTI IA

==============================

def nova5_compare(prompt): results = {}

results["OPENAI"] = ask_openai(prompt)
results["CLAUDE"] = ask_claude(prompt)
results["GEMINI"] = ask_gemini(prompt)

response = "🤖 NOVA5 — MULTI IA


---

"

for model, text in results.items():
    response += f"🧠 {model}

{text}


---

"

response += "Nova5 actif."

return response

==============================

TELEGRAM

==============================

def send_telegram(chat_id, text): requests.post( f"{TELEGRAM_URL}/sendMessage", json={ "chat_id": chat_id, "text": text } )

@app.route("/webhook", methods=["POST"]) def webhook(): data = request.json

if "message" not in data:
    return jsonify({"ok": True})

chat_id = data["message"]["chat"]["id"]
text = data["message"].get("text", "")

if text.startswith("/compare"):
    question = text.replace("/compare", "").strip()

    send_telegram(chat_id, "Nova5 analyse multi-IA...")

    response = nova5_compare(question)

    send_telegram(chat_id, response)

else:
    send_telegram(
        chat_id,
        "Nova5 actif. Commande principale : /compare ta question"
    )

return jsonify({"ok": True})

@app.route("/health") def health(): return jsonify({ "status": "ok", "openai": bool(OPENAI_API_KEY), "claude": bool(CLAUDE_API_KEY), "gemini": bool(GEMINI_API_KEY) })

if name == "main": app.run(host="0.0.0.0", port=8080)
