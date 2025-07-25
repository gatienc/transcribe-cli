# Transcribe CLI

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A Command Line Interface (CLI) application for audio transcription, text translation, leveraging the Mistral AI API.

## ✨ Features

- **Audio Transcription:** Transcribes audio from the microphone.
  - Interactive recording: Start/stop with Enter, cancel with Escape.
  - Recording duration guardrail: Prompts for confirmation if recording exceeds 30 seconds.
  - **Copy to Clipboard:** Option to automatically copy transcription to clipboard.
- **Text Translation:** Translates text using Mistral's chat models.
- **Model Selection:** Defaults to cost-effective Mistral AI models, with an option (`--large-model`) to use larger models.

## 🚀 Setup

1.  **Clone the repository:**

    ```bash
    git clone git@github.com:gatienc/transcribe-cli.git
    cd transcribe-cli
    ```

2.  **Configure Mistral AI API Key:**
    Obtain your API key from [Mistral AI Platform](https://console.mistral.ai/api-keys).
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

- **Transcribe Audio:**

  ```bash
  transcribe record
  ```

  (Press Enter to stop, Escape to cancel)

- **Transcribe:**  
   `transcribe record --to-clipboard`

- **Translate:**  
   `transcribe translate "<text>" --target-language <lang>`

- **Change Tone:**  
   `transcribe change-tone "<text>" --custom-tone-prompt "<prompt>"`

- **Large Model:**  
   Add `--large-model` before any command.

## 🤝 Contributing

Contributions are welcome.

## 📄 License

MIT License.
