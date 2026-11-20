from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def call_gemini(prompt, model):
    client = genai.Client(  # reads GEMINI_API_KEY
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=3)
        )
    )
    resp = client.models.generate_content(model=model, contents=prompt)
    usage = resp.usage_metadata
    # Thinking tokens are billed as output tokens, so they are included.
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return resp.text, usage.prompt_token_count, output_tokens
