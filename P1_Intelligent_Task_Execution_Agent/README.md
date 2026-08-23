# Nexa AI — Intelligent Task Execution Agent

A premium Streamlit AI assistant that demonstrates the **Intelligent Task Execution Agent** architecture from the supplied project diagram.

## Architecture

User → Streamlit UI → Agent → Task analysis → Tool selection → Tool execution → Observe → Continue/Finish → Final response

The agent uses modern LangChain `create_agent`, which implements a graph-based agent runtime with an iterative model/tool loop. Tools are ordinary Python functions decorated with `@tool`.

## Included features

- Deep Teal + Soft Mint + White premium UI
- Responsive ChatGPT-style chat interface
- Modern sidebar/navigation
- Dashboard metric cards
- History and Favorites
- Light/Dark mode
- Tool execution trace
- Reference/source cards
- Empty, loading, and error states
- Typing indicator
- Hover/card/button micro-animations
- Calculator tool
- Current-time tool
- Optional live web-search tool
- LangChain tool calling
- ReAct-style iterative execution

## 1. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install packages

```bash
pip install -r requirements.txt
```

## 3. Configure the API key

Copy `.env.example` to `.env` and add your OpenAI API key.

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

Then load `.env` automatically by adding this at the very top of `app.py` if needed:

```python
from dotenv import load_dotenv
load_dotenv()
```

The simplest alternative is to set the environment variable directly in PowerShell:

```powershell
$env:OPENAI_API_KEY="your_key"
```

## 4. Run

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit.

## 5. Demo prompts

Try:

- `Calculate 1250 * 0.18 + 750`
- `What time is it?`
- `Research the latest trends in AI agents and summarize them with sources.`
- `Create a 7-step learning plan for Python and LangChain.`

## Important

The web-search tool uses DuckDuckGo through the `ddgs` package. If it fails in your environment, calculator and time tools still work.

For deployment, store `OPENAI_API_KEY` as a secret/environment variable rather than committing `.env`.
