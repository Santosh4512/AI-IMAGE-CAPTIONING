# AI Image Captioning Web Application

A modern Streamlit web application that lets users upload an image, analyze it with Google's Gemini multimodal AI, and generate high-quality captions in different styles and lengths.

## Project Overview

This project is designed as a final-year CSE portfolio application. The app allows users to:

- Upload images in JPG, JPEG, PNG, and WEBP formats
- Choose caption styles and lengths
- Add custom instructions for more tailored outputs
- Generate captions with the Google Gemini vision model
- Copy or download the result
- Review generation history in the current session

## Features

- Drag-and-drop image upload
- Validation for file type and file size
- Display of image metadata including dimensions and size
- Gemini-powered caption generation using a modern vision-capable model
- Caption customization by style and length
- Optional user-specific instruction field
- Results section with caption preview, copy action, and TXT download
- Session-based caption history
- Clear image/reset flow
- Responsive, polished UI built with Streamlit and custom CSS

## Technologies Used

- Python 3.9+
- Streamlit
- Google Gen AI SDK (`google-genai`)
- Pillow
- python-dotenv

## Folder Structure

```text
ai-image-captioning/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── services/
│   ├── __init__.py
│   └── gemini_service.py
└── utils/
    ├── __init__.py
    └── image_utils.py
```

## Prerequisites

Before running the app, make sure you have:

- Python 3.9 or later
- A Google Gemini API key
- A local terminal or VS Code integrated terminal

## Python Virtual Environment Setup

```bash
cd "AI IMAGE CAPTIONING"
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
cd "AI IMAGE CAPTIONING"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Dependency Installation

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Gemini API Key Configuration

Create a local `.env` file in the project root using the example file:

```bash
cp .env.example .env
```

Then update `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

You can also configure the key in Streamlit secrets:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Important:

- Never commit your `.env` or `.streamlit/secrets.toml` files to GitHub.
- Add them to `.gitignore` before pushing.
- The key is read from the environment or Streamlit secrets at runtime.

## How to Run the Application

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, typically:

```text
http://localhost:8501
```

## Example Usage

1. Upload a landscape, portrait, product image, or everyday scene.
2. Choose a caption style such as "Professional" or "Creative".
3. Pick a length such as short, medium, or long.
4. Add optional custom instructions.
5. Click "Generate Caption".
6. Review, copy, or download the output.

## Common Errors and Troubleshooting

### 1. Missing Gemini API key

You will see a warning in the UI if the API key is not configured.

Fix:

- Add `GEMINI_API_KEY` to `.env`
- Or configure `.streamlit/secrets.toml`

### 2. Unsupported model error

This app checks for a modern vision-capable Gemini model and falls back to a current supported option when possible.

If the API still rejects the model:

- Check your Gemini API access and quota
- Ensure your account has access to the model family
- Verify you are using the current `google-genai` SDK version

### 3. File upload rejected

Supported formats:

- JPG
- JPEG
- PNG
- WEBP

The app rejects invalid file types and oversized files.

### 4. Network or quota issues

If the request fails because of connectivity or quota limits, the app displays a user-friendly error rather than crashing.

## Screenshots

Add project screenshots to a folder like `screenshots/` and reference them here:

```md
![Upload Screen](screenshots/upload.png)
![Generated Caption](screenshots/result.png)
```

## Future Enhancements

- Multi-image comparison captions
- Batch captioning for folders
- Text-to-image prompt suggestions
- Save caption history to a database
- User authentication and account-based history
- Support for multilingual captions

## License

This project is meant for educational and portfolio purposes.

## Notes for Interview Explanation

This project demonstrates:

- Full-stack Python app development
- API integration with a cloud AI service
- Good file validation and error handling
- Practical UI/UX design thinking
- Application architecture that separates concerns between UI, services, and utilities
