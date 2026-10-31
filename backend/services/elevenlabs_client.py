"""
ElevenLabs Client — Text-to-Speech for the ghost's voice.
Uses direct async HTTP calls via httpx to avoid heavy SDK dependencies and Windows path length limits.
"""

import base64
import httpx
import sentry_sdk

from config import get_settings


class ElevenLabsClient:
    """Client for ElevenLabs TTS — giving the ghost a voice."""

    # Spooky-ish voice presets available on free tier
    VOICE_MAP = {
        "aria": "9BWtsMINqrJLrRacOk9x",       # Aria — smooth, ethereal
        "roger": "CwhRBWXzGAHq8TQ4Fs17",       # Roger — deep, older
        "sarah": "EXAVITQu4vr4xnSDxMaL",       # Sarah — soft, whispery
        "laura": "FGY2WhTYpPnrIDTdsKH5",       # Laura — calm, narrative
        "charlie": "IKne3meq5aSn9XLyUdCD",     # Charlie — warm, storytelling
    }

    DEFAULT_VOICE = "aria"
    BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.elevenlabs_api_key

    @sentry_sdk.trace
    async def speak_ghost(self, text: str, voice: str = "aria") -> dict:
        """
        Convert ghost text to speech and return as base64 audio.

        Returns:
            dict with 'audio_base64' (data URI) and 'content_type'
        """
        if not self.api_key:
            return {"audio_base64": "", "content_type": "", "error": "ElevenLabs API key not configured"}

        voice_id = self.VOICE_MAP.get(voice, self.VOICE_MAP[self.DEFAULT_VOICE])
        url = f"{self.BASE_URL}/{voice_id}"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text[:1000],  # Cap at 1000 chars for free tier
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.75,
                "style": 0.2,
                "use_speaker_boost": True,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                audio_bytes = response.content

            b64 = base64.b64encode(audio_bytes).decode("utf-8")
            data_uri = f"data:audio/mpeg;base64,{b64}"

            return {
                "audio_base64": data_uri,
                "content_type": "audio/mpeg",
            }

        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"audio_base64": "", "content_type": "", "error": str(e)}

