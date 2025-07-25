import logging
import os
import queue
import wave
from pathlib import Path
from typing import Optional, Tuple

import requests
import sounddevice as sd
import soundfile as sf
from pynput import keyboard

from .constants import (
    CHANNELS,
    DEFAULT_CHAT_MODEL,
    DEFAULT_TRANSCRIPTION_MODEL,
    LARGE_CHAT_MODEL,
    LARGE_TRANSCRIPTION_MODEL,
    MISTRAL_CHAT_API_URL,
    MISTRAL_TRANSCRIPTION_API_URL,
    SAMPLE_RATE,
    WAVE_OUTPUT_FILENAME,
)


class Transcriber:
    """
    A CLI application for real-time audio transcription and translation using the Mistral API.
    """

    def __init__(self, use_large_model: bool = False) -> None:
        """
        Initializes the Transcriber with API key and audio settings.

        Parameters
        ----------
        use_large_model : bool, optional
            If True, use larger, more capable (and potentially more expensive) models.
            Defaults to False.
        """
        self.mistral_api_key: Optional[str] = os.getenv("MISTRAL_API_KEY")
        if not self.mistral_api_key or self.mistral_api_key == "VOTRE_CLÉ_API_ICI":
            raise ValueError(
                "MISTRAL_API_KEY is not configured. Please set it in the .env file."
            )
        self.logger = logging.getLogger(__name__)
        self.transcription_model = (
            LARGE_TRANSCRIPTION_MODEL
            if use_large_model
            else DEFAULT_TRANSCRIPTION_MODEL
        )
        self.chat_model = (
            LARGE_CHAT_MODEL if use_large_model else DEFAULT_CHAT_MODEL
        )
        self.logger.info(
            f"Using transcription model: {self.transcription_model}")
        self.logger.info(f"Using chat model: {self.chat_model}")

    def record_audio(self) -> Tuple[bool, float]:
        output_path = Path(WAVE_OUTPUT_FILENAME)
        if output_path.exists():
            output_path.unlink()
        q: queue.Queue[any] = queue.Queue()
        recording = True
        cancelled = False

        def on_press(key):
            nonlocal recording
            nonlocal cancelled
            if key == keyboard.Key.enter:
                recording = False
                return False
            if key == keyboard.Key.esc:
                recording = False
                cancelled = True
                return False

        def callback(indata, frames, time, status):
            if status:
                self.logger.warning(status)
            q.put(indata.copy())

        try:
            with sf.SoundFile(
                str(output_path),
                mode="x",
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
            ) as file:
                with sd.InputStream(
                    samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback
                ) as stream:
                    print("Recording... Press Enter to stop or Esc to cancel.")
                    with keyboard.Listener(on_press=on_press) as listener:
                        while recording:
                            file.write(q.get())
                        listener.join()

            if cancelled:
                if output_path.exists():
                    output_path.unlink()
                return False, 0.0

            if output_path.exists():
                with wave.open(str(output_path), "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
                return True, duration

        except Exception as e:
            self.logger.error(f"An error occurred during recording: {e}")

        return False, 0.0

    def transcribe_audio(self) -> str:
        """
        Transcribes an audio file using the Mistral Voxstral API.

        This method reads the temporary audio file, sends it to the Mistral
        API for transcription, and then deletes the temporary file.

        Returns
        -------
        str
            The transcribed text returned by the API.

        Raises
        -------
        requests.exceptions.RequestException
            If the API call fails.
        """
        headers = {"Authorization": f"Bearer {self.mistral_api_key}"}
        audio_path = Path(WAVE_OUTPUT_FILENAME)

        if not audio_path.exists():
            raise FileNotFoundError(
                "Audio file not found. Recording may have failed.")

        try:
            with open(audio_path, "rb") as f:
                files = {
                    "file": (audio_path.name, f, "audio/wav"),
                    "model": (None, self.transcription_model),
                }
                self.logger.info(
                    "Sending audio to Mistral API for transcription...")
                response = requests.post(
                    MISTRAL_TRANSCRIPTION_API_URL, headers=headers, files=files
                )
                response.raise_for_status()
                self.logger.info("Transcription received.")
                return response.json().get("text", "No transcription data returned.")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API Error: {e}")
            if e.response is not None:
                self.logger.error(f"Response body: {e.response.text}")
            raise
        finally:
            # Clean up the temporary file
            if audio_path.exists():
                audio_path.unlink()

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translates the given text to the target language using Mistral's chat completions API.

        Parameters
        ----------
        text : str
            The text to be translated.
        target_language : str
            The language to translate the text into (e.g., "French", "Spanish").

        Returns
        -------
        str
            The translated text.

        Raises
        -------
        requests.exceptions.RequestException
            If the API call fails.
        """
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [
            {
                "role": "user",
                "content": f"Translate the following text to {target_language}:\n\n{text}",
            }
        ]
        payload = {
            "model": self.chat_model,
            "messages": messages,
        }

        self.logger.info(f"Translating text to {target_language}...")
        try:
            response = requests.post(
                MISTRAL_CHAT_API_URL, headers=headers, json=payload
            )
            response.raise_for_status()
            translated_text = response.json(
            )["choices"][0]["message"]["content"]
            self.logger.info("Translation received.")
            return translated_text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API Error during translation: {e}")
            if e.response is not None:
                self.logger.error(f"Response body: {e.response.text}")
            raise

    def change_tone(self, text: str, custom_tone_prompt: str) -> str:
        """
        Rephrases the given text to the specified tone using Mistral's chat completions API.

        Parameters
        ----------
        text : str
            The text to be rephrased.
        custom_tone_prompt : str
            A custom prompt describing the desired tone (e.g., 'Rephrase this as an angry email').

        Returns
        -------
        str
            The rephrased text.

        Raises
        -------
        requests.exceptions.RequestException
            If the API call fails.
        """
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }

        self.logger.info(
            f"Changing tone with custom prompt: '{custom_tone_prompt}'...")
        full_prompt = f"{custom_tone_prompt}\n\n{text}"

        messages = [
            {
                "role": "user",
                "content": full_prompt,
            }
        ]
        payload = {
            "model": self.chat_model,
            "messages": messages,
        }

        try:
            response = requests.post(
                MISTRAL_CHAT_API_URL, headers=headers, json=payload
            )
            response.raise_for_status()
            rephrased_text = response.json(
            )["choices"][0]["message"]["content"]
            self.logger.info("Tone change received.")
            return rephrased_text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API Error during tone change: {e}")
            if e.response is not None:
                self.logger.error(f"Response body: {e.response.text}")
            raise
