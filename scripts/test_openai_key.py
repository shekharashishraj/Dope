#!/usr/bin/env python3
"""Minimal API key check for OpenAI SDK."""
import os
import sys
from openai import OpenAI


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set")
        return 2

    model = os.getenv("OPENAI_TEST_MODEL", "gpt-5.1-2025-11-13")
    client = OpenAI(api_key=api_key)

    try:
        resp = client.responses.create(
            model=model,
            input="Reply with the single word: OK",
        )
        text = getattr(resp, "output_text", None) or ""
        print("SUCCESS: API call completed")
        print("model", model)
        print("response", text.strip()[:80])
        return 0
    except Exception as exc:
        print("ERROR: API call failed")
        print("model", model)
        print("error", str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
