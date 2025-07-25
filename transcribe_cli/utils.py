import logging
import pyperclip

def _output_transcription(transcription: str, to_clipboard: bool, logger: logging.Logger) -> None:
    """
    Helper function to print and optionally copy transcription to clipboard.
    """
    print("\n--- Transcription ---")
    print(transcription)
    print("---------------------")
    if to_clipboard:
        try:
            pyperclip.copy(transcription)
            logger.info("Transcription copied to clipboard.")
        except pyperclip.PyperclipException as e:
            logger.error(f"Failed to copy to clipboard: {e}")

