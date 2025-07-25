from pathlib import Path

# Audio settings
SAMPLE_RATE: int = 16000  # 16kHz
CHANNELS: int = 1  # Mono
FORMAT: str = "S16_LE"  # 16-bit little-endian, standard for WAV
WAVE_OUTPUT_FILENAME: str = "temp_recording.wav"

# Mistral API settings
MISTRAL_TRANSCRIPTION_API_URL: str = "https://api.mistral.ai/v1/audio/transcriptions"
MISTRAL_CHAT_API_URL: str = "https://api.mistral.ai/v1/chat/completions"

# Model names
DEFAULT_TRANSCRIPTION_MODEL: str = "voxtral-mini-2507"
LARGE_TRANSCRIPTION_MODEL: str = "voxtral-large-latest"  # Placeholder for a larger model
DEFAULT_CHAT_MODEL: str = "mistral-small-latest"
LARGE_CHAT_MODEL: str = "mistral-large-latest"

# Tone rephrasing prompts
TONE_CONTEXTS_DIR: Path = Path(__file__).parent.parent / "tone_contexts"
