if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY missing")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing")
