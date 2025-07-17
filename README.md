# Transcribe CLI

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A Command Line Interface (CLI) application for audio transcription, text translation, and tone rephrasing, leveraging the Mistral AI API.

## ✨ Features

*   **Audio Transcription:** Transcribes audio from the microphone.
    *   Interactive recording: Start/stop with Enter, cancel with Escape.
    *   Recording duration guardrail: Prompts for confirmation if recording exceeds 30 seconds.
    *   **Copy to Clipboard:** Option to automatically copy transcription to clipboard.
*   **Text Translation:** Translates text using Mistral's chat models.
*   **Tone Rephrasing:** Adjusts text tone based on a user-defined custom prompt.
*   **Model Selection:** Defaults to cost-effective Mistral AI models, with an option (`--large-model`) to use larger models.
*   **Logging:** Utilizes Python's `logging` module for output.
*   **Dependency Management:** Uses `uv` for package management.

## 🚀 Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/transcribe-cli.git
    cd transcribe-cli
    ```

2.  **Configure Mistral AI API Key:**
    Obtain your API key from [Mistral AI Platform](https://console.mistral.ai/).
    Create a `.env` file in the project root and add your API key:
    ```
    MISTRAL_API_KEY="YOUR_MISTRAL_API_KEY_HERE"
    ```

3.  **Install dependencies and activate environment:**
    If `uv` is not installed:
    ```bash
    pip install uv
    ```
    Create and activate a `uv` managed environment, then install the project:
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install .
    ```
    This installs the package, making the `transcribe` command directly available in your activated terminal session.

## 💡 Usage

Once the environment is activated (as per setup step 3), you can run commands directly:

*   **Transcribe Audio:**
    ```bash
    transcribe record
    ```
    (Press Enter to stop, Escape to cancel)

*   **Transcribe Audio and Copy to Clipboard:**
    ```bash
    transcribe record --to-clipboard
    ```

*   **Translate Text:**
    ```bash
    transcribe translate "Hello, how are you?" --target-language French
    ```

*   **Change Text Tone:**
    ```bash
    transcribe change-tone "This is a simple sentence." --custom-tone-prompt "Rephrase this as an angry email."
    ```

*   **Use Larger Models:**
    Add `--large-model` before the command:
    ```bash
    transcribe --large-model record
    ```

## 📚 Commands Reference

### `record`

Records audio from the default microphone and transcribes it.

```bash
transcribe record
```

*   `--to-clipboard`: Copy the transcription to the system clipboard.

### `translate <text> --target-language <language>`

Translates `<text>` to the specified `--target-language`. Default target is `English`.

```bash
transcribe translate "Je voudrais traduire cette phrase." --target-language English
```

### `change-tone <text> --custom-tone-prompt <prompt>`

Rephrases `<text>` using a custom tone prompt.

*   `<text>`: The text whose tone needs to be changed.
*   `--custom-tone-prompt`: A custom prompt describing the desired tone (e.g., 'Rephrase this as an angry email'). This argument is required.

```bash
transcribe change-tone "Can you help me with this?" --custom-tone-prompt "Make this sound very formal and polite."
```

### Global Option: `--large-model`

When used, selects larger (potentially more expensive) Mistral AI models for all operations.

```bash
transcribe --large-model translate "Hello." --target-language Spanish
```

## ⚙️ Configuration

`MISTRAL_API_KEY` is loaded from `.env`.

## ⚠️ OS Compatibility & Dependencies

This CLI has been developed and tested exclusively on **Linux** systems.

The `record` command relies on the `arecord` utility, which is part of the **ALSA utilities** (`alsa-utils` package on Debian/Ubuntu-based systems). This is a hard dependency for audio recording.

```bash
# On Debian/Ubuntu-based systems:
sudo apt-get install alsa-utils
```

**Windows & macOS Support:**
The current implementation of the `record` command (using `arecord` and `termios`/`tty` for interactive input) is **not compatible** with Windows or macOS.

We are open to contributions or issue reports from users interested in extending compatibility to other operating systems. If you'd like to help or have suggestions for cross-platform audio recording and interactive input, please open an issue on the GitHub repository.

## 🤝 Contributing

Contributions are welcome.

## 📄 License

MIT License.
