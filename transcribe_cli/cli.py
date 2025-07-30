import argparse
import logging
import subprocess
import sys
from typing import Optional

import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv  # Added import

from .transcriber import Transcriber
from .utils import _output_transcription
from .constants import AUDIO_TOO_LONG_THRESHOLD_SECONDS

# Load environment variables
load_dotenv()

# Configure logging (moved from transcriber.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _get_user_confirmation(logger: logging.Logger) -> Optional[bool]:
    while True:
        try:
            confirm = input(
                "Do you want to proceed with transcription (y) or delete the recording (d)? "
            ).lower()
            if confirm == "y":
                return True
            elif confirm == "d":
                return False
            else:
                logger.warning(f"Invalid input: {confirm}. Please enter 'y' or 'd'.")
        except EOFError:
            logger.error("Input stream closed unexpectedly. Assuming 'd' for delete.")
            return False
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user. Recording deleted.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during user input: {e}")
            return False


def handle_record_command(args: argparse.Namespace) -> None:
    transcriber = Transcriber(use_large_model=args.large_model)
    try:
        recording_successful, duration_seconds = transcriber.record_audio()
        if recording_successful:
            if duration_seconds > AUDIO_TOO_LONG_THRESHOLD_SECONDS:
                transcriber.logger.warning(
                    f"Recording duration ({duration_seconds:.2f}s) is longer than {AUDIO_TOO_LONG_THRESHOLD_SECONDS} seconds."
                )
                proceed = _get_user_confirmation(transcriber.logger)
                if proceed:
                    transcription = transcriber.transcribe_audio()
                    _output_transcription(
                        transcription, args.to_clipboard, transcriber.logger
                    )
                else:
                    transcriber.logger.info("Recording deleted due to length.")
            else:
                transcription = transcriber.transcribe_audio()
                _output_transcription(
                    transcription, args.to_clipboard, transcriber.logger
                )
        else:
            transcriber.logger.info("Recording cancelled.")
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        requests.exceptions.RequestException,
        ValueError,
    ) as e:
        logger.error(f"Transcription failed: {e}")
    finally:
        transcriber.cleanup()


def handle_translate_command(args: argparse.Namespace) -> None:
    transcriber = Transcriber(use_large_model=args.large_model)
    try:
        translated_text = transcriber.translate_text(args.text, args.target_language)
        print(f"\n--- Translated Text ({args.target_language}) ---")
        print(translated_text)
        print("---------------------")
    except requests.exceptions.RequestException as e:
        logger.error(f"Translation failed: {e}")


def handle_change_tone_command(args: argparse.Namespace) -> None:
    transcriber = Transcriber(use_large_model=args.large_model)
    try:
        rephrased_text = transcriber.change_tone(
            args.text, custom_tone_prompt=args.custom_tone_prompt
        )
        print("\n--- Rephrased Text ---")
        print(rephrased_text)
        print("---------------------")
    except requests.exceptions.RequestException as e:
        logger.error(f"Tone change failed: {e}")
    except ValueError as e:
        logger.error(f"Tone change failed: {e}")


def main() -> None:
    """
    Main function to handle command-line arguments and run the transcription or translation process.
    """
    parser = argparse.ArgumentParser(
        description="A CLI application for real-time audio transcription and translation using the Mistral API."
    )

    parser.add_argument(
        "--large-model",
        action="store_true",
        help="Use larger, more capable (and potentially more expensive) models.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Record command
    record_parser = subparsers.add_parser(
        "record", help="Record audio and transcribe it."
    )
    record_parser.add_argument(
        "--to-clipboard",
        action="store_true",
        help="Copy the transcription to the system clipboard.",
    )
    record_parser.set_defaults(func=lambda args: handle_record_command(args))

    # Translate command
    translate_parser = subparsers.add_parser(
        "translate", help="Translate text using Mistral API."
    )
    translate_parser.add_argument("text", type=str, help="The text to be translated.")
    translate_parser.add_argument(
        "--target-language",
        type=str,
        default="English",
        help="The language to translate the text into (e.g., 'French', 'Spanish'). Default is English.",
    )
    translate_parser.set_defaults(func=lambda args: handle_translate_command(args))

    # Change Tone command
    change_tone_parser = subparsers.add_parser(
        "change-tone", help="Change the tone of a given text."
    )
    change_tone_parser.add_argument(
        "text", type=str, help="The text whose tone needs to be changed."
    )

    change_tone_parser.add_argument(
        "--custom-tone-prompt",
        type=str,
        required=True,
        help="A custom prompt describing the desired tone (e.g., 'Rephrase this as an angry email').",
    )

    change_tone_parser.set_defaults(func=lambda args: handle_change_tone_command(args))

    args = parser.parse_args()

    if args.command:
        try:
            args.func(args)
        except (
            FileNotFoundError,
            subprocess.CalledProcessError,
            requests.exceptions.RequestException,
            ValueError,
        ) as e:
            logger.error(f"An error occurred: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
