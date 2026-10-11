import json
import os
from html import escape
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from services.gemini_service import GeminiCaptionService
from utils.image_utils import format_file_size, get_image_metadata, validate_image_file

load_dotenv()

st.set_page_config(
    page_title="AI Image Captioning",
    page_icon="🖼️",
    layout="wide",
)


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #090909;
            --panel: #121212;
            --panel-alt: #1b1a17;
            --primary: #d4af37;
            --primary-dark: #b88f1a;
            --text: #f8f2df;
            --muted: #c0b18d;
            --border: rgba(212,175,55,0.26);
            --success: #b7a06b;
            --warning: #f1c75b;
            --danger: #e08b63;
        }

        .stApp {
            background: radial-gradient(circle at top, rgba(212,175,55,0.18), transparent 28%), linear-gradient(180deg, #060606 0%, #0d0d0d 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero-card {
            background: linear-gradient(135deg, rgba(212,175,55,0.18), rgba(255,255,255,0.01));
            border: 1px solid rgba(212,175,55,0.35);
            border-radius: 22px;
            padding: 2rem 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 18px 40px rgba(0,0,0,0.35);
        }

        .hero-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin: 0.6rem 0 1rem 0;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            background: rgba(212,175,55,0.12);
            color: #f9ebbf;
            border: 1px solid rgba(212,175,55,0.28);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 0 4px rgba(16,185,129,0.15);
        }

        .section-card {
            background: rgba(18,18,18,0.9);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.2rem;
            box-shadow: 0 10px 28px rgba(0,0,0,0.28);
        }

        .info-banner {
            background: rgba(212,175,55,0.06);
            border: 1px solid rgba(212,175,55,0.2);
            border-radius: 12px;
            padding: 0.8rem 0.9rem;
            margin-top: 0.9rem;
            color: var(--text);
        }

        .metric-box {
            background: var(--panel-alt);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.8rem;
            margin-top: 0.6rem;
        }

        .tiny-label {
            font-size: 0.77rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .caption-box {
            background: rgba(20,20,20,0.9);
            border: 1px solid rgba(212,175,55,0.18);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            min-height: 120px;
            white-space: pre-wrap;
            line-height: 1.7;
            color: var(--text);
        }

        div[data-testid="stFileUploader"] > section {
            background: linear-gradient(180deg, rgba(212,175,55,0.07), rgba(18,18,18,0.9));
            border: 1.5px dashed rgba(212,175,55,0.5);
            border-radius: 16px;
            padding: 1rem;
        }

        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
            transition: transform 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
        }

        .stDownloadButton > button {
            border-radius: 12px;
            font-weight: 600;
        }

        .primary-cta {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white !important;
            border: none !important;
        }

        .developer-footer {
            margin-top: 2rem;
            padding: 1rem 0 0.5rem;
            text-align: center;
            border-top: 1px solid rgba(212,175,55,0.2);
            color: var(--muted);
            font-size: 0.92rem;
        }

        .developer-footer a {
            color: #f9ebbf;
            text-decoration: none;
            font-weight: 600;
        }

        .developer-footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            .hero-card {
                padding: 1.4rem 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []
    if "generated_caption" not in st.session_state:
        st.session_state.generated_caption = ""
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    if "image_info" not in st.session_state:
        st.session_state.image_info = {}


def add_to_history(caption: str, style: str, length: str) -> None:
    entry = {
        "caption": caption,
        "style": style,
        "length": length,
    }
    history = st.session_state.get("history", [])
    history.insert(0, entry)
    st.session_state.history = history[:5]


def reset_state() -> None:
    st.session_state.current_image = None
    st.session_state.image_info = {}
    st.session_state.generated_caption = ""
    st.session_state.history = []


def render_header() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="tiny-label">AI Vision Demo</div>
            <div class="hero-badges">
                <span class="status-pill"><span class="status-dot"></span> Gemini Ready</span>
                <span class="status-pill">Image-to-Text AI</span>
                <span class="status-pill">Portfolio-Ready</span>
            </div>
            <h1 style="margin: 0.25rem 0 0.4rem 0; font-size: 2.6rem; color: #0f172a;">AI Image Captioning</h1>
            <p style="margin: 0; font-size: 1.08rem; color: #475569;">Turn your images into meaningful descriptions with AI.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_section() -> None:
    st.markdown("<div class='tiny-label'>1. Image Upload</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "webp"],
        help="Supported formats: JPG, JPEG, PNG, and WEBP. Maximum size: 15 MB.",
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        try:
            validated = validate_image_file(uploaded_file)
            st.session_state.current_image = uploaded_file.getvalue()
            st.session_state.image_info = validated
            st.session_state.generated_caption = ""

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.image(
                    uploaded_file,
                    caption=f"{validated['filename']} • {validated['dimensions']} • {validated['file_size']}",
                    use_container_width=True,
                )
            with col2:
                st.write("<div class='tiny-label'>Image Details</div>", unsafe_allow_html=True)
                st.write(f"**File name:** {validated['filename']}")
                st.write(f"**Type:** {validated['mime_type']}")
                st.write(f"**Dimensions:** {validated['dimensions']}")
                st.write(f"**File size:** {validated['file_size']}")
                st.write(f"**Format:** {validated['format']}")
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class='info-banner'>
                    ✅ Image validated and ready for AI caption generation.
                </div>
                """,
                unsafe_allow_html=True,
            )
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.current_image = None
            st.session_state.image_info = {}


def render_settings_section() -> None:
    st.markdown("<div class='tiny-label'>2. Caption Settings</div>", unsafe_allow_html=True)
    with st.container():
        style = st.selectbox(
            "Caption style",
            [
                "Short and simple",
                "Detailed description",
                "Professional",
                "Creative",
                "Social media",
            ],
            index=0,
        )
        length = st.radio("Caption length", ["Short", "Medium", "Long"], horizontal=True)
        custom_instruction = st.text_area(
            "Custom instruction (optional)",
            value="",
            placeholder="Example: Focus on the mood, objects, and setting visible in the photo.",
            help="Add more guidance for the model without making up details.",
        )

        try:
            streamlit_secret_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
        except Exception:
            streamlit_secret_key = ""
        api_key = os.getenv("GEMINI_API_KEY") or streamlit_secret_key
        if not api_key:
            st.warning(
                "API key not configured yet. Set GEMINI_API_KEY in your environment or in .streamlit/secrets.toml to enable caption generation."
            )

        generate_clicked = st.button(
            "Generate Caption",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.get("current_image"),
        )
        if st.session_state.get("current_image"):
            st.markdown(
                "<div class='info-banner'>Ready to generate a caption using the selected style and length.</div>",
                unsafe_allow_html=True,
            )

        if generate_clicked:
            if not st.session_state.get("current_image"):
                st.warning("Please upload an image before generating a caption.")
            elif not api_key:
                st.warning("The Gemini API key is missing. Add it to continue.")
            else:
                try:
                    with st.spinner("Analyzing the image and generating a caption..."):
                        service = GeminiCaptionService(api_key=api_key)
                        caption = service.generate_caption(
                            image_bytes=st.session_state.current_image,
                            mime_type=st.session_state.image_info["mime_type"],
                            style=style,
                            length=length,
                            custom_instruction=custom_instruction,
                        )
                    st.session_state.generated_caption = caption
                    add_to_history(caption, style, length)
                    st.success("Caption generated successfully.")
                except Exception as exc:
                    st.error(f"Caption generation failed: {exc}")


def render_results_section() -> None:
    st.markdown("<div class='tiny-label'>3. Generated Result</div>", unsafe_allow_html=True)

    if st.session_state.generated_caption:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        col_left, col_right = st.columns([1.15, 0.85])

        with col_left:
            st.write("**Caption:**")
            st.markdown(
                f"<div class='caption-box'>{st.session_state.generated_caption}</div>",
                unsafe_allow_html=True,
            )

        with col_right:
            if st.session_state.current_image:
                st.write("**Uploaded Image:**")
                st.image(st.session_state.current_image, use_container_width=True)

        if st.button("Copy Caption", use_container_width=True):
            caption_json = json.dumps(st.session_state.generated_caption)
            components.html(
                f"""
                <script>
                const text = JSON.parse({caption_json});
                navigator.clipboard.writeText(text)
                    .then(() => {{
                        const toast = document.createElement('div');
                        toast.textContent = 'Caption copied to clipboard!';
                        toast.style.position = 'fixed';
                        toast.style.bottom = '20px';
                        toast.style.right = '20px';
                        toast.style.zIndex = '9999';
                        toast.style.background = '#111827';
                        toast.style.color = '#ffffff';
                        toast.style.padding = '10px 16px';
                        toast.style.borderRadius = '12px';
                        toast.style.fontSize = '14px';
                        toast.style.boxShadow = '0 10px 20px rgba(15, 23, 42, 0.18)';
                        document.body.appendChild(toast);
                        setTimeout(() => toast.remove(), 1800);
                    }})
                    .catch(() => alert('Copy failed. You can copy the caption manually from the result panel.'));
                </script>
                """,
                height=0,
            )
            st.toast("Caption copied to clipboard.")

        st.download_button(
            label="Download Caption (.txt)",
            data=st.session_state.generated_caption,
            file_name="image_caption.txt",
            mime="text/plain",
            use_container_width=True,
        )

        if st.button("Clear and Start Again", use_container_width=True):
            reset_state()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class='section-card'>
                <p style='color: #475569; margin: 0;'>Upload an image and generate a caption to see the result here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_history() -> None:
    st.markdown("<div class='tiny-label'>Recent History</div>", unsafe_allow_html=True)
    if not st.session_state.history:
        st.info("No captions generated yet in this session.")
        return

    for item in st.session_state.history:
        history_label = escape(f"{item['style']} • {item['length']}")
        history_caption = escape(item["caption"])
        st.markdown(
            f"""
            <div class='section-card' style='margin-top: 0.8rem;'>
                <div class='tiny-label'>{history_label}</div>
                <p style='margin: 0.5rem 0 0; color: #0f172a;'>{history_caption}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    inject_custom_css()
    initialize_session_state()
    render_header()

    col_upload, col_settings = st.columns([1.25, 0.75], gap="large")
    with col_upload:
        render_upload_section()
    with col_settings:
        render_settings_section()

    render_results_section()
    render_history()

    st.markdown(
        """
        <div class="developer-footer">
            <div>Developed By : <a href="https://www.instagram.com/santoshbhashkarreddy_/" target="_blank" rel="noopener noreferrer">Santosh Bhashkar Reddy</a></div>
            <div style="margin-top: 0.25rem;">
                <a href="https://www.instagram.com/santoshbhashkarreddy_/" target="_blank" rel="noopener noreferrer">Instagram</a>
                &nbsp;|&nbsp;
                <a href="https://www.linkedin.com/in/santosh-bhashkar-reddy-nallamilli-696b5a330/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
