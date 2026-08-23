# AURELIA — Automated Document Processing System

Project 4: Document upload → parsing → chunking → ChromaDB retrieval → Groq extraction → Pydantic validation → automatic re-processing → structured output.

## Windows quick start

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and add your real Groq API key.

Then:

```bat
streamlit run app.py
```

Supported: PDF, DOCX, TXT.

Never commit `.env` or your API key to GitHub.
