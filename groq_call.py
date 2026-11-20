"""Groq call: returns (reply, input_tokens, output_tokens)."""
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def call_groq(prompt, model):
    client = Groq()  # reads GROQ_API_KEY
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return (
        resp.choices[0].message.content,
        resp.usage.prompt_tokens,
        resp.usage.completion_tokens,
    )
