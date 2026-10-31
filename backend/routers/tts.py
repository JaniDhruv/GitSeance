"""
TTS Router — ElevenLabs Text-to-Speech endpoint for ghost voice.
"""

from fastapi import APIRouter, HTTPException
import sentry_sdk

from models.schemas import TTSRequest, TTSResponse
from services.elevenlabs_client import ElevenLabsClient

router = APIRouter(prefix="/api/tts", tags=["tts"])

tts_client = ElevenLabsClient()


@router.post("/speak", response_model=TTSResponse)
async def speak_ghost(request: TTSRequest):
    """
    Convert a ghost's message to speech using ElevenLabs.
    
    Returns a base64-encoded audio data URI that the frontend
    can play directly.
    """

    with sentry_sdk.start_transaction(op="tts", name="speak_ghost"):
        try:
            result = await tts_client.speak_ghost(
                text=request.text,
                voice=request.voice,
            )

            if result.get("error"):
                raise HTTPException(
                    status_code=503,
                    detail=f"The ghost lost its voice: {result['error']}"
                )

            return TTSResponse(
                audio_url=result["audio_base64"],
            )

        except HTTPException:
            raise
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise HTTPException(
                status_code=500,
                detail=f"Voice synthesis failed: {str(e)}"
            )
