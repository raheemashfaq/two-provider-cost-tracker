# Two provider cost tracker

Sends the same prompt to Google Gemini and Groq, then prints each reply and a
table of input tokens, output tokens, seconds and cost in USD. It also saves
`results.json` with one object per provider.

## Run

```bash
uv sync
cp .env.example .env      # then put your real keys in .env
uv run tracker.py "Explain tokens in one sentence."
```

Keys, model names and prices (USD per 1M tokens) all live in `.env`; see
`.env.example`. Token counts come from each API's usage data, never estimated.
Cost = input_tokens x input_price / 1,000,000 + output_tokens x output_price / 1,000,000.

## Sample output

```
provider     input  output  seconds    cost (USD)
gemini           7     416   116.80      0.001565
groq            77     119     1.16      0.000041
```

## What I learned

The same sentence cost 7 input tokens on Gemini and 77 on Groq, because each
model tokenizes differently (and the Groq model adds its own chat template).
Output tokens cost several times more than input tokens, and Gemini's
"thinking" tokens are billed as output, which made its reply far more
expensive and slower than Groq's even though both answers were one sentence.
