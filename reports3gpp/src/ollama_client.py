"""Simple client for communicating with an Ollama server.

The implementation is deliberately lightweight – it uses the ``requests``
library (already a dependency of the project) to POST a prompt to the
``/api/generate`` endpoint and returns the generated text.

Usage example::

    from ollama_client import query_ollama
    response = query_ollama("http://10.95.118.26", "gpt-oss:120b", "Hola, que tal estas?")
    print(response)

No explicit error handling is performed as per the current requirements; any
exception will propagate to the caller.
"""

from __future__ import annotations

import json
import requests
from json import JSONDecodeError
from typing import Any

__all__ = ["query_ollama"]


def query_ollama(host: str, model: str, prompt: str, temperature: float = 0.0) -> str:
    """Send a prompt to an Ollama server and return the generated response.

    Args:
        host: Base URL of the Ollama server (e.g. ``http://10.95.118.26``).
        model: The model name to use (e.g. ``gpt-oss:120b``).
        prompt: The prompt string to send.
        temperature: Sampling temperature for the model (default 0.0).

    Returns:
        The generated text response from the model.
    """
    url = f"{host.rstrip('/')}/api/generate"
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
    }
    # Ollama returns a JSON object with a ``response`` field containing the text.
    resp = requests.post(url, json=payload, stream=True)
    resp.raise_for_status()
    # Ollama may return a stream of JSON objects, each containing a ``response``
    # fragment. We collect all fragments and concatenate them.
    full_response = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except JSONDecodeError:
            # Fallback: try to parse the line as a complete JSON object.
            obj = json.loads(line.strip())
        # Some responses use the key ``response``; others may use ``content``.
        fragment = obj.get("response") or obj.get("content") or ""
        full_response.append(fragment)
    return "".join(full_response)
