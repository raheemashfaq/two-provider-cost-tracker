"""Send one prompt to Gemini and Groq, then compare reply, tokens, time and cost."""
import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq

load_dotenv()


def require_env(*names):
    """Exit with a clear message if any variable is missing from .env."""
    missing = [n for n in names if not os.getenv(n)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}. See .env.example.")


def call_gemini(prompt, model):
    client = genai.Client(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=3)
        )
    )
    resp = client.models.generate_content(model=model, contents=prompt)
    usage = resp.usage_metadata
    # Thinking tokens are billed as output tokens, so they are included.
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return resp.text, usage.prompt_token_count, output_tokens


def call_groq(prompt, model):
    client = Groq()
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return (
        resp.choices[0].message.content,
        resp.usage.prompt_tokens,
        resp.usage.completion_tokens,
    )


def cost(tokens, price_per_million):
    return tokens * price_per_million / 1_000_000


def run_provider(name, prompt, call):
    """Time one provider call and build its results.json entry."""
    prefix = name.upper()
    model = os.environ[f"{prefix}_MODEL"]
    in_price = float(os.environ[f"{prefix}_INPUT_PRICE_PER_M"])
    out_price = float(os.environ[f"{prefix}_OUTPUT_PRICE_PER_M"])

    start = time.perf_counter()
    reply, in_tok, out_tok = call(prompt, model)
    seconds = time.perf_counter() - start

    return {
        "provider": name,
        "model": model,
        "reply": reply,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "input_price_per_m": in_price,
        "output_price_per_m": out_price,
        "cost_usd": cost(in_tok, in_price) + cost(out_tok, out_price),
        "seconds": round(seconds, 2),
    }


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: uv run tracker.py "your prompt"')
    prompt = " ".join(sys.argv[1:])

    require_env(
        "GEMINI_API_KEY", "GROQ_API_KEY",
        "GEMINI_MODEL", "GEMINI_INPUT_PRICE_PER_M", "GEMINI_OUTPUT_PRICE_PER_M",
        "GROQ_MODEL", "GROQ_INPUT_PRICE_PER_M", "GROQ_OUTPUT_PRICE_PER_M",
    )
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

    results = []
    for name, call in (("gemini", call_gemini), ("groq", call_groq)):
        try:
            results.append(run_provider(name, prompt, call))
        except Exception as e:
            print(f"[{name}] call failed: {e}", file=sys.stderr)

    for r in results:
        print(f"\n=== {r['provider']} ({r['model']}) ===\n{r['reply']}")

    print(f"\n{'provider':<10}{'input':>8}{'output':>8}{'seconds':>9}{'cost (USD)':>14}")
    for r in results:
        print(f"{r['provider']:<10}{r['input_tokens']:>8}{r['output_tokens']:>8}"
              f"{r['seconds']:>9.2f}{r['cost_usd']:>14.6f}")

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    if len(results) < 2:
        sys.exit(1)


if __name__ == "__main__":
    main()
