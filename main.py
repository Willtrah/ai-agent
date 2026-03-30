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

# Mode par chat
# "auto" = une IA choisie automatiquement
# "multi" = les 3 IA à chaque question
CHAT_MODES = {}

# ==============================
# HELPERS
# ==============================

def send_telegram(chat_id, text):
    if not TELEGRAM_TOKEN:
        return

    chunks = [text[i:i+3900] for i in range(0, len(text), 3900)]

    for chunk in chunks:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": chunk
            },
            timeout=60
        )


def get_chat_mode(chat_id):
    return CHAT_MODES.get(chat_id, "auto")


def set_chat_mode(chat_id, mode):
    CHAT_MODES[chat_id] = mode


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
# ROUTING AUTO
# ==============================

def choose_best_model(prompt):
    p = prompt.lower()

    code_keywords = [
        "code", "python", "javascript", "js", "html", "css",
        "bug", "erreur", "api", "script", "fonction", "programme",
        "railway", "telegram", "flask", "sql"
    ]

    fast_keywords = [
        "résume", "resume", "résumé", "summary", "court",
        "traduis", "traduis", "translate", "reformule",
        "simple", "vite", "rapide", "short"
    ]

    deep_keywords = [
        "analyse", "stratégie", "strategie", "vision", "philosophie",
        "raisonnement", "futur", "comparaison", "compare",
        "business", "plan", "architecture", "concept"
    ]

    if any(k in p for k in code_keywords):
        return "openai"

    if any(k in p for k in fast_keywords):
        return "gemini"

    if any(k in p for k in deep_keywords):
        return "claude"

    return "claude"


def ask_auto(prompt):
    model = choose_best_model(prompt)

    if model == "openai":
        answer = ask_openai(prompt)
        return f"🤖 NOVA5 — MODE AUTO\n\n🧠 IA choisie: OPENAI\n\n{answer}"

    if model == "gemini":
        answer = ask_gemini(prompt)
        return f"🤖 NOVA5 — MODE AUTO\n\n🧠 IA choisie: GEMINI\n\n{answer}"

    answer = ask_claude(prompt)
    return f"🤖 NOVA5 — MODE AUTO\n\n🧠 IA choisie: CLAUDE\n\n{answer}"


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
# TELEGRAM WEBHOOK
# ==============================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if not data or "message" not in data:
        return jsonify({"ok": True})

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    mode = get_chat_mode(chat_id)

    # /start
    if text == "/start":
        send_telegram(
            chat_id,
            "Nova5 actif.\n\n"
            "Commandes :\n"
            "/multi on  → active les 3 IA en permanence\n"
            "/multi off → retour au mode auto\n"
            "/status    → voir le mode actuel\n"
            "/compare question → comparaison ponctuelle\n\n"
            "Sans /compare :\n"
            "- si multi = ON → 3 IA répondent\n"
            "- si multi = OFF → Nova5 choisit la meilleure IA automatiquement"
        )
        return jsonify({"ok": True})

    # /status
    if text == "/status":
        send_telegram(
            chat_id,
            f"🤖 NOVA5 — STATUS\n\nMode actuel : {mode.upper()}"
        )
        return jsonify({"ok": True})

    # /multi on
    if text == "/multi on":
        set_chat_mode(chat_id, "multi")
        send_telegram(
            chat_id,
            "✅ Mode MULTI activé.\n\nToutes tes prochaines questions seront envoyées à OpenAI + Claude + Gemini."
        )
        return jsonify({"ok": True})

    # /multi off
    if text == "/multi off":
        set_chat_mode(chat_id, "auto")
        send_telegram(
            chat_id,
            "✅ Mode AUTO activé.\n\nNova5 choisira automatiquement l’IA la plus adaptée pour chaque question."
        )
        return jsonify({"ok": True})

    # /compare ponctuel
    if text.startswith("/compare"):
        question = text.replace("/compare", "", 1).strip()

        if not question:
            send_telegram(chat_id, "Utilise : /compare ta question")
            return jsonify({"ok": True})

        send_telegram(chat_id, "Nova5 analyse multi-IA...")
        response = nova5_compare(question)
        send_telegram(chat_id, response)
        return jsonify({"ok": True})

    # Question normale
    if mode == "multi":
        send_telegram(chat_id, "Nova5 analyse multi-IA...")
        response = nova5_compare(text)
        send_telegram(chat_id, response)
    else:
        send_telegram(chat_id, "Nova5 choisit la meilleure IA...")
        response = ask_auto(text)
        send_telegram(chat_id, response)

    return jsonify({"ok": True})


# ==============================
# HEALTH
# ==============================

@app.route("/", methods=["GET"])
def home():
    return "Nova5 AI Server Running"


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
