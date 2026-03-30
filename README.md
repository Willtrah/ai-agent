# ai-agent

Railway-ready AI agent starter with:
- Flask health endpoints (`/`, `/health`, `/status`)
- Background heartbeat worker
- Telegram bot polling in background
- Environment-variable based secret loading

Required variables:
- TELEGRAM_BOT_TOKEN
- OPENAI_API_KEY (optional for boot, recommended)
- GEMINI_API_KEY (optional)
- ANTHROPIC_API_KEY (optional)
