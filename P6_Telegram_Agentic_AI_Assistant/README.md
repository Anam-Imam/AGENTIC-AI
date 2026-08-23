# LUXE FLOW — Telegram Agentic AI Assistant

A single-file Telegram + Streamlit agentic AI project using Groq and LangGraph.

## 1. Create environment

Windows CMD:

```bat
python -m venv .venv
.venv\Scripts\activate
```

## 2. Install

```bat
python -m pip install -r requirements.txt
```

## 3. Configure

Copy `.env.example` to `.env` and add:

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_MODEL=llama-3.3-70b-versatile
```

Never put these values in frontend JavaScript or commit `.env` to Git.

## 4. Run

```bat
streamlit run app.py
```

The browser opens the Luxe Flow studio. The Telegram polling bot starts automatically in the same `app.py` process when `TELEGRAM_BOT_TOKEN` is configured.

## 5. Test Telegram

Open your bot in Telegram and send:

`/start`

Then send a normal message such as:

`Explain LangGraph in simple words`

or:

`Calculate 125 * 24`

## Workflow

Telegram message
→ LangGraph analyze
→ optional tool/knowledge
→ Groq reasoning
→ validation
→ Telegram response

The project intentionally keeps the Telegram bot in `app.py`; there is no separate `telegram_bot.py`.
