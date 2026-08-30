#google_speech_agent.py

"""
Google Cloud Speech-to-Text transcription (V1 API).

Fixes vs. the original snippet:
1. `encoding=LINEAR16` was declared while feeding the API raw uploaded
   bytes (mp3/wav/m4a/webm/ogg/flac) unchanged. LINEAR16 means
   uncompressed 16-bit PCM - sending compressed audio while claiming
   LINEAR16 is a real format mismatch and produces exactly the kind of
   garbled output you'd otherwise blame on "bad transcription." Audio is
   now converted to real 16kHz mono LINEAR16 PCM via pydub/ffmpeg first,
   which also means we don't need to know or trust the original file
   extension.
2. `model="latest_long"` + `use_enhanced=True` are not guaranteed for
   every V1 language - only "default" and "command_and_search" are
   guaranteed across all supported languages (Amharic and Oromo included).
   Switched to "default".
3. Synchronous `client.recognize()` is capped at ~1 minute of audio.
   Voice notes for this app can run longer, so this now uses
   `long_running_recognize()`.
4. `language_code` parameter now takes the same short codes ("en"/"am"/
   "om") used everywhere else in this project (app.py passes
   `lang_code`), instead of a mismatched full BCP-47 default.
5. Unused `io`/`base64` imports removed; added error handling so a
   credentials or quota failure surfaces a clear message instead of
   crashing the Streamlit app.

Requires: `pip install google-cloud-speech pydub` and the `ffmpeg`
binary available on PATH (pydub shells out to it for format
conversion). Also requires GOOGLE_APPLICATION_CREDENTIALS to be set to
a service-account key with Speech-to-Text access.

Note on language coverage: Amharic (am-ET) is confirmed supported on
Speech-to-Text V1. Oromo (om-ET) support is broader and generally more
accurate via Google's newer Chirp models, which live on the V2 API
(`google.cloud.speech_v2`, model="chirp_2"/"chirp_3"). If Oromo
transcription quality is weak here, that's the next thing to migrate.
"""

import os
import tempfile

from google.cloud import speech_v1
from google.cloud.speech_v1 import types
from pydub import AudioSegment

TARGET_SAMPLE_RATE = 16000

LANG_MAP = {
    "en": "en-US",
    "am": "am-ET",
    "om": "om-ET",
}


def _to_linear16_wav(audio_bytes: bytes) -> bytes:
    """
    Convert arbitrary uploaded audio into mono 16kHz LINEAR16 PCM WAV
    bytes. pydub/ffmpeg detects the source format from the file content
    itself, so the caller doesn't need to pass along an extension.
    """
    src_path = None
    dst_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as src:
            src.write(audio_bytes)
            src_path = src.name

        segment = AudioSegment.from_file(src_path)
        segment = segment.set_channels(1).set_frame_rate(TARGET_SAMPLE_RATE)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as dst:
            dst_path = dst.name
        segment.export(dst_path, format="wav")

        with open(dst_path, "rb") as f:
            return f.read()
    finally:
        for path in (src_path, dst_path):
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass


def transcribe_audio(audio_bytes: bytes, language: str = "am") -> str:
    """
    Transcribe audio using Google Cloud Speech-to-Text (V1).
    Supports Amharic ("am"), Oromo ("om"), and English ("en") - same
    short language codes used by the rest of this project.
    """
    if len(audio_bytes) < 1000:
        raise ValueError("Audio file is too small or empty")

    language_code = LANG_MAP.get(language, "am-ET")

    try:
        wav_bytes = _to_linear16_wav(audio_bytes)
    except Exception as e:
        raise ValueError(f"Could not decode audio file: {e}") from e

    try:
        client = speech_v1.SpeechClient()
    except Exception as e:
        raise RuntimeError(
            f"Could not create Speech-to-Text client - check "
            f"GOOGLE_APPLICATION_CREDENTIALS: {e}"
        ) from e

    audio = types.RecognitionAudio(content=wav_bytes)
    config = types.RecognitionConfig(
        encoding=types.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=TARGET_SAMPLE_RATE,
        language_code=language_code,
        enable_automatic_punctuation=True,
        # "default" is guaranteed across all supported languages;
        # "latest_long"/enhanced models are not guaranteed for
        # lower-resource languages like Amharic/Oromo on V1.
        model="default",
    )

    try:
        # long_running_recognize (not recognize) because sync recognize()
        # is capped at ~1 minute of audio and a voice note can exceed that.
        operation = client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=180)
    except Exception as e:
        raise RuntimeError(f"Speech-to-Text request failed: {e}") from e

    transcript = " ".join(
        result.alternatives[0].transcript
        for result in response.results
        if result.alternatives
    ).strip()

    if not transcript:
        raise ValueError("No speech detected in audio")

    return transcript