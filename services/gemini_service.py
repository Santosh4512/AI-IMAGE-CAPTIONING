import os
from typing import Optional

from google import genai
from google.genai import types


class GeminiCaptionService:
    """Generate image captions using the Google Gemini vision model."""

    DEFAULT_MODEL_CANDIDATES = (
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-pro-latest",
    )

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or self._read_streamlit_secret()
        if not self.api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY. Add it to your environment or .streamlit/secrets.toml."
            )

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:  # pragma: no cover - SDK initialization path
            raise RuntimeError(f"Unable to initialize Gemini client: {exc}") from exc

        self.model_name = self.resolve_model_name()

    @staticmethod
    def _read_streamlit_secret() -> Optional[str]:
        try:
            import streamlit as st

            if hasattr(st, "secrets"):
                return st.secrets.get("GEMINI_API_KEY")
        except Exception:
            return None
        return None

    def get_available_model_names(self):
        try:
            page = self.client.models.list()
            items = getattr(page, "items", None)
            if items is None:
                items = list(page)
        except Exception:
            return []

        names = []
        for item in items:
            name = getattr(item, "name", str(item))
            if name.startswith("models/"):
                name = name.split("/", 1)[1]
            names.append(name)
        return names

    def resolve_model_name(self) -> str:
        available = self.get_available_model_names()
        for candidate in self.DEFAULT_MODEL_CANDIDATES:
            if candidate in available:
                return candidate

        for candidate in available:
            if "gemini" in candidate.lower():
                return candidate

        return self.DEFAULT_MODEL_CANDIDATES[0]

    def build_prompt(
        self,
        style: str,
        length: str,
        custom_instruction: str = "",
    ) -> str:
        style_prompt_map = {
            "Short and simple": "Keep the caption brief, clear, and easy to understand. Use plain language.",
            "Detailed description": "Describe visible objects, actions, setting, colors, and atmosphere in a natural way.",
            "Professional": "Write a polished, concise, professional caption suitable for reports or portfolios.",
            "Creative": "Make the caption vivid and expressive while staying grounded in what is visible.",
            "Social media": "Write an engaging, modern caption appropriate for social sharing and attention-grabbing hooks.",
        }

        length_prompt_map = {
            "Short": "Keep it around 10 to 20 words.",
            "Medium": "Keep it around 25 to 50 words.",
            "Long": "Keep it around 60 to 100 words, but remain precise and grounded in the image.",
        }

        prompt = (
            "You are an expert image captioning assistant. "
            "Describe only what is clearly visible in the image. "
            "Do not invent people, places, events, emotions, or details that are not supported by the image. "
            f"Caption style: {style}. {style_prompt_map.get(style, '')} "
            f"Length: {length}. {length_prompt_map.get(length, 'Keep it factual and concise.')} "
            "Return a single polished caption in plain English."
        )

        if custom_instruction.strip():
            prompt += f" Additional instruction: {custom_instruction.strip()}"

        return prompt

    @staticmethod
    def _is_retryable_api_error(message: str) -> bool:
        lower = message.lower()
        return (
            "quota" in lower
            or "limit" in lower
            or "429" in lower
            or "503" in lower
            or "unavailable" in lower
            or "high demand" in lower
            or "too many requests" in lower
            or "temporarily unavailable" in lower
        )

    @staticmethod
    def _format_api_error(exc: Exception) -> RuntimeError:
        message = str(exc).lower()
        if "quota" in message or "limit" in message or "429" in message:
            return RuntimeError("Gemini API quota or rate limit reached. Please try again later.")
        if "unsupported" in message or "not found" in message or "404" in message:
            return RuntimeError(
                "The configured Gemini model is unavailable. Please verify the model access in your Google AI account."
            )
        if "unavailable" in message or "503" in message or "high demand" in message:
            return RuntimeError(
                "Gemini is currently busy with high demand. Please wait a moment and try again."
            )
        if "network" in message or "timeout" in message or "connection" in message:
            return RuntimeError("Network error while contacting the Gemini API. Please check your connection and try again.")
        return RuntimeError(f"Gemini caption generation failed: {exc}")

    def generate_caption(
        self,
        image_bytes: bytes,
        mime_type: str,
        style: str = "Short and simple",
        length: str = "Medium",
        custom_instruction: str = "",
    ) -> str:
        if not image_bytes:
            raise ValueError("The uploaded image is empty.")

        prompt = self.build_prompt(style, length, custom_instruction)

        candidate_models = [self.model_name]
        for candidate in self.DEFAULT_MODEL_CANDIDATES:
            if candidate not in candidate_models:
                candidate_models.append(candidate)

        last_exception: Optional[Exception] = None
        response = None

        for model_name in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        top_p=0.8,
                        max_output_tokens=300,
                        system_instruction=(
                            "You are a helpful image captioning assistant. "
                            "Prioritize accuracy, clarity, and factual detail. "
                            "Do not invent unseen elements."
                        ),
                    ),
                )
                break
            except Exception as exc:
                last_exception = exc
                if model_name != candidate_models[-1]:
                    continue
                raise self._format_api_error(exc) from exc

        if response is None:
            if last_exception is not None:
                raise self._format_api_error(last_exception) from last_exception
            raise RuntimeError("Gemini caption generation failed unexpectedly.")

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        candidates = getattr(response, "candidates", []) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content is None:
                continue
            parts = getattr(content, "parts", []) or []
            collected = []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    collected.append(part_text)
            if collected:
                return "\n".join(collected).strip()

        raise RuntimeError("The Gemini API returned an empty caption. Please try a different image or settings.")
