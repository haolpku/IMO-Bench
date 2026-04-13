"""
API client using curl subprocess to call OpenAI-compatible endpoints.
Avoids issues with security software blocking Python HTTP libraries.
"""

import json
import subprocess
import time


def call_api(base_url: str, api_key: str, model: str, prompt: str,
             max_retries: int = 5, temperature: float = 0.7,
             max_tokens: int = 32768, timeout: int = 300) -> str:
    """Call an OpenAI-compatible chat completion API via curl."""
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "--max-time", str(timeout),
                    url,
                    "-H", f"Authorization: Bearer {api_key}",
                    "-H", "Content-Type: application/json",
                    "-d", payload_json,
                ],
                capture_output=True, text=True, timeout=timeout + 60,
            )
            if result.returncode != 0:
                raise RuntimeError(f"curl exit {result.returncode}: {result.stderr}")

            resp = json.loads(result.stdout)
            if "error" in resp:
                raise RuntimeError(f"API error: {resp['error']}")

            return resp["choices"][0]["message"]["content"]

        except Exception as e:
            wait = min(2 ** attempt * 5, 120)
            print(f"\n  [Retry {attempt+1}/{max_retries}] {e}. Waiting {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"Failed after {max_retries} retries")
