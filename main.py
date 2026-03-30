import os
import time
import logging

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("AI Multi-Agent System Started")

# =============================
# API KEYS (FROM RAILWAY VARIABLES)
# =============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# =============================
# SECURITY CHECK
# =============================

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing")

if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY missing")

if not CLAUDE_API_KEY:
    logging.warning("CLAUDE_API_KEY missing")

# =============================
# SYSTEM CONFIG
# =============================

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4.1-mini")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gemini-2.5-flash")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", "/app/memory.db")

# =============================
# PERFORMANCE CONFIG
# =============================

LOW_RAM_MODE = os.getenv("LOW_RAM_MODE", "true")
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", 3))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 5))

MAX_MEMORY_ITEMS = int(os.getenv("MAX_MEMORY_ITEMS", 10000))
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", 120))

# =============================
# MAIN LOOP
# =============================

def main():
    logging.info("AI Agent Running...")
    
    while True:
        try:
            logging.info("Heartbeat OK")
            time.sleep(60)

        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
