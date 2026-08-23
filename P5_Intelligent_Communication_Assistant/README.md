# ✦ AURA — Intelligent Communication Assistant

A premium Streamlit implementation of **Project 5 — Intelligent Communication Assistant**.

## Architecture

User → Streamlit UI → Groq Agent / Decision Making → SMTP Email or Pushover Notification → Confirmation / Logs → Streamlit UI

## Features

- Groq-powered situation analysis
- AI decision making for channel, urgency and tone
- Prepared email/push communication
- Direct email sending from the app after entering the recipient and clicking Send Email Now
- SMTP email tool with direct in-app sending
- Pushover notification tool
- Confirmation and local logs
- History and favorites
- Animated AI orb and floating UI
- Light/dark visual mode
- Responsive glassmorphism interface
- API keys kept server-side in `.env`

## 1. Create environment

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

## 2. Install dependencies

```bat
pip install -r requirements.txt
```

## 3. Configure secrets

Copy `.env.example` to `.env`:

```bat
copy .env.example .env
```

Then add your Groq API key.

Optional tools:
- SMTP: add `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL`
- Pushover: add `PUSHOVER_TOKEN` and `PUSHOVER_USER`

## 4. Run

```bat
streamlit run app.py
```

## Important

The AI only prepares the communication. The actual Send Email / Push Notification action requires the user to click the corresponding button.

Never commit `.env` to GitHub.

## Project structure

```text
intelligent_communication_assistant/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── (runtime JSON logs)
└── services/
    ├── __init__.py
    ├── groq_agent.py
    ├── notifications.py
    └── storage.py
```


## Direct SMTP email

The recipient is entered directly inside the AURA interface. The SMTP account in `.env`
is the sender account; the recipient does NOT need to be stored in `.env`.

For Gmail, use:
- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME=your Gmail address`
- `SMTP_PASSWORD=your Google App Password`
- `SMTP_FROM_EMAIL=your Gmail address`

Do not use your normal Gmail password when Google requires an App Password.
