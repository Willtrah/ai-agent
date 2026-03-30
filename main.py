import os
import time
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("AI Multi-Agent System Started")

TELEGRAM_TOKEN = os.getenv("8720929752:AAG7V-v9U9TmvgBOa1-MzCKJ66vqO-0VF4o")
OPENAI_API_KEY = os.getenv("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")
GEMINI_API_KEY = os.getenv("AIzaSyCDp997Ul6iTxub3BFhEOCWa3sujTNIl5E")
ANTHROPIC_API_KEY = os.getenv("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")

def health_check():
    logging.info("System running...")
    logging.info(f"Telegram: {'OK' if TELEGRAM_TOKEN else 'Missing'}")
    logging.info(f"OpenAI: {'OK' if OPENAI_API_KEY else 'Missing'}")
    logging.info(f"Gemini: {'OK' if GEMINI_API_KEY else 'Missing'}")
    logging.info(f"Anthropic: {'OK' if ANTHROPIC_API_KEY else 'Missing'}")


def main():
    logging.info("AI Agent Booting...")

    while True:
        try:
            health_check()
            time.sleep(60)

        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
