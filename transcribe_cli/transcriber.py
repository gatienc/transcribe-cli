import logging
import os # Added os import
import subprocess
import sys
import termios
import tty
import wave
from pathlib import Path
from typing import Optional, Tuple

import requests

from .constants import (
    CHANNELS,
    DEFAULT_CHAT_MODEL,
    DEFAULT_TRANSCRIPTION_MODEL,
    FORMAT,
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
        """
        Records audio using ALSA `arecord` until Enter or Escape is pressed.

        This method starts `arecord` as a background process to capture audio.
        It sets the terminal to cbreak mode to read single key presses.
        If Enter is pressed, the recording stops and the file is kept.
        If Escape is pressed, the recording stops and the file is deleted.

        Returns
        -------
        Tuple[bool, float]
            A tuple containing:
            - bool: True if recording was successful (Enter pressed), False if cancelled (Escape pressed).
            - float: The duration of the recorded audio in seconds, or 0.0 if cancelled or failed.

        Raises
        -------
        FileNotFoundError
            If the `arecord` command is not found.
        Exception
            If any other error occurs during recording.
        """
        output_path = Path(WAVE_OUTPUT_FILENAME)
        command = [
            "arecord",
            "-D",
            "default",
            "-q",
            "-r",
            str(SAMPLE_RATE),
            "-c",
            str(CHANNELS),
            "-f",
            FORMAT,
            "-t",
            "wav",
            str(output_path),
        ]

        old_settings = termios.tcgetattr(sys.stdin)
        recording_successful = False
        recorder_process = None
        duration_seconds = 0.0

        try:
            # Set terminal to cbreak mode so we can read single key presses
            tty.setcbreak(sys.stdin.fileno())
            # Start the recording process in the background
            recorder_process = subprocess.Popen(command)

            self.logger.info(
                "Recording... Press Enter to stop, Escape to cancel.")

            while True:
                char = sys.stdin.read(1)
                if char == '\n':  # Enter key
                    recording_successful = True
                    break
                elif char == '\x1b':  # Escape key
                    recording_successful = False
                    break

        except FileNotFoundError:
            self.logger.error("Error: `arecord` command not found.")
            self.logger.error(
                "Please ensure ALSA tools are installed (`sudo apt-get install alsa-utils`)."
            )
            raise
        except Exception as e:
            self.logger.error(f"An error occurred during recording: {e}")
            raise
        finally:
            # Always restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

            if recorder_process and recorder_process.poll() is None:
                recorder_process.terminate()
                recorder_process.wait()

            self.logger.info("Recording stopped.")

            if not recording_successful and output_path.exists():
                output_path.unlink()
                self.logger.info("Recording cancelled and file deleted.")
            elif recording_successful and output_path.exists():
                try:
                    with wave.open(str(output_path), 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        if rate > 0:
                            duration_seconds = frames / float(rate)
                except wave.Error as e:
                    self.logger.error(
                        f"Error reading WAV file for duration: {e}")
                    duration_seconds = 0.0

        return recording_successful, duration_seconds

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
