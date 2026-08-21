import json
import time
import requests
import google.generativeai as genai
from app.ai.provider import AIProvider
from app.core.config import settings
from app.core.logging import logger

# transient network errors typical of a MITM/inspection proxy truncating streamed responses
_TRANSIENT_ERRORS = (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)


class GeminiNetworkBlockedError(RuntimeError):
    """Raised when a network intermediary (proxy/firewall) blocks the Gemini API call, not Gemini itself."""


def _raise_if_network_blocked(exc: Exception) -> None:
    # a genuine Gemini/Google error body is JSON; an HTML body means a proxy/firewall intercepted the request
    message = str(exc)
    if "<html" in message.lower():
        raise GeminiNetworkBlockedError(
            "Request to generativelanguage.googleapis.com was intercepted and blocked by a network "
            "proxy/firewall (HTML response instead of a JSON API error). This is a network policy issue, "
            "not a code or API key problem. Contact IT to allowlist generativelanguage.googleapis.com."
        ) from exc


def _call_with_retry(fn, *args, retries: int = 3, backoff_seconds: float = 1.5, **kwargs):
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except _TRANSIENT_ERRORS as e:
            last_error = e
            logger.warning(f"Gemini call failed with {type(e).__name__} (attempt {attempt}/{retries}), retrying...")
            time.sleep(backoff_seconds * attempt)
        except Exception as e:
            _raise_if_network_blocked(e)
            raise
    raise last_error


class GeminiProvider(AIProvider):
    def __init__(self):
        self._configured = bool(settings.gemini_api_key)
        if self._configured:
            genai.configure(api_key=settings.gemini_api_key, transport="rest")
            self._model = genai.GenerativeModel(settings.gemini_model)

    def is_configured(self) -> bool:
        return self._configured

    async def generate(self, prompt: str, context: str = "") -> str:
        if not self._configured:
            raise RuntimeError("Gemini API key not configured")

        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        try:
            response = _call_with_retry(self._model.generate_content, full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {type(e).__name__}")
            raise

    async def generate_structured(self, prompt: str, context: str = "") -> dict:
        if not self._configured:
            raise RuntimeError("Gemini API key not configured")

        json_prompt = (
            f"{context}\n\n{prompt}\n\n"
            "IMPORTANT: Respond with valid JSON only. No markdown, no code fences, no explanation outside the JSON."
        )
        try:
            response = _call_with_retry(self._model.generate_content, json_prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Gemini returned non-JSON response, wrapping as raw text")
            return {"raw_response": response.text}
        except Exception as e:
            logger.error(f"Gemini structured generation failed: {type(e).__name__}")
            raise


gemini_provider = GeminiProvider()