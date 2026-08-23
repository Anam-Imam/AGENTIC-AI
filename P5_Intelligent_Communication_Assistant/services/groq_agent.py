import json
import os
import uuid
from datetime import datetime

from groq import Groq


SYSTEM_PROMPT = """
You are AURA, an Intelligent Communication Assistant.
Your job is to analyze an event/situation and prepare an appropriate communication.
You may recommend email or push notification. Do not send anything yourself.
Return ONLY valid JSON with this exact structure:
{
  "decision": {
    "title": "...",
    "channel": "Email or Push notification",
    "urgency": "Low, Normal, High, or Critical",
    "tone": "...",
    "reason": "..."
  },
  "communication": {
    "recipient": "...",
    "subject": "...",
    "body": "...",
    "short_message": "..."
  },
  "alternatives": ["...", "..."]
}
Keep the communication practical and concise. If recipient details are unknown, use a safe placeholder such as "recipient@example.com".
"""


class CommunicationAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def analyze(self, situation, channel, audience, urgency, tone):
        if not self.client:
            raise RuntimeError("GROQ_API_KEY is missing. Add it to .env and restart Streamlit.")

        user_prompt = f"""
Situation:
{situation}

Requested channel: {channel}
Audience: {audience}
Urgency: {urgency}
Tone: {tone}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.25,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        data["id"] = str(uuid.uuid4())[:8]
        data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["input"] = {
            "situation": situation,
            "channel": channel,
            "audience": audience,
            "urgency": urgency,
            "tone": tone,
        }
        return data
