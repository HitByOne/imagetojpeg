import streamlit as st
from PIL import Image
import os
import zipfile
import shutil
import datetime
import pytz

# Page configuration
st.set_page_config(
    page_title="Image to JPG Converter",
    page_icon="🖼️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem 1rem;
    }
    .stTitle {
        text-align: center;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .info-box {
        padding: 1rem;
        background-color: #e2e3e5;
        border: 1px solid #d6d8db;
        border-radius: 0.5rem;
        color: #383d41;
        text-align: center;
    }
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        flex-wrap: wrap;
    }
    .stat-item {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        min-width: 120px;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0066cc;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("# 🖼️ Image to JPG Converter")
st.markdown("""
    <div class="subtitle">
        Convert your images to JPG format instantly
    </div>
""", unsafe_allow_html=True)

cst_timezone = pytz.timezone("America/Chicago")
current_time_cst = datetime.datetime.now(cst_timezone)

output_folder = "converted_files"
zip_filename = "converted_images.zip"

def cleanup_files():
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

def convert_image_to_jpg(uploaded_file, output_path):
    """
    Convert an uploaded image file to JPG.
    PNG files are always placed on a white background before conversion.
    Transparency in WEBP, GIF, and other alpha-capable formats is also handled.
    TIF/TIFF files are supported, including multi-page (only first page is converted).
    """
    with Image.open(uploaded_file) as img:
        image_format = (img.format or "").upper()
        image_mode = img.mode

        # PNG: always flatten onto white background before converting to JPEG
        if image_format == "PNG":
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            white_bg = Image.new("RGB", img.size, (255, 255, 255))
            white_bg.paste(img, mask=img.getchannel("A"))
            img = white_bg

        # WEBP: normalize first, then flatten if transparency exists
        elif image_format == "WEBP":
            if img.mode in ("RGBA", "LA", "P"):
                if img.mode == "P":
                    img = img.convert("RGBA")
                elif img.mode == "LA":
                    img = img.convert("RGBA")

                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                white_bg.paste(img, mask=img.getchannel("A"))
                img = white_bg
            else:
                img = img.convert("RGB")

        # TIFF: handle multi-page (use first frame), high bit-depth, and transparency
        elif image_format in ("TIFF", "TIF"):
            # Seek to first frame if multi-page
            try:
                img.seek(0)
            except EOFError:
                pass

            # Handle high bit-depth (e.g. 16-bit grayscale or RGB)
            if img.mode in ("I", "I;16", "I;16B", "F"):
                import numpy as np
                arr = np.array(img, dtype=np.float32)
                arr = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255).astype(np.uint8)
                img = Image.fromarray(arr).convert("RGB")
            elif img.mode in ("RGBA", "LA", "P"):
                if img.mode == "P":
                    img = img.convert("RGBA")
                elif img.mode == "LA":
                    img = img.convert("RGBA")

                if "A" in img.getbands():
                    white_bg = Image.new("RGB", img.size, (255, 255, 255))
                    white_bg.paste(img, mask=img.getchannel("A"))
                    img = white_bg
                else:
                    img = img.convert("RGB")
            else:
                img = img.convert("RGB")

        # GIF / transparent images / palette images
        elif image_mode in ("RGBA", "LA", "P"):
            if img.mode == "P":
                img = img.convert("RGBA")
            elif img.mode == "LA":
                img = img.convert("RGBA")

            if "A" in img.getbands():
                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                white_bg.paste(img, mask=img.getchannel("A"))
                img = white_bg
            else:
                img = img.convert("RGB")

        # Everything else
        else:
            img = img.convert("RGB")

        img.save(output_path, "JPEG", quality=95, optimize=True)

st.markdown("### 📁 Select Images to Convert")
uploaded_files = st.file_uploader(
    "Choose image files (JPG, JPEG, PNG, BMP, GIF, WEBP, TIF, TIFF)",
    type=["jpg", "jpeg", "png", "bmp", "gif", "webp", "tif", "tiff"],
    accept_multiple_files=True,
    help="Select one or more image files to convert to JPG format"
)

if uploaded_files:
    cleanup_files()
    os.makedirs(output_folder, exist_ok=True)

    successful_conversions = []
    failed_conversions = []

    st.markdown("### ⚙️ Converting Images...")
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing: {uploaded_file.name}")

            base_name = os.path.splitext(uploaded_file.name)[0]
            output_filename = f"{base_name}.jpg"

            existing_names = set(successful_conversions)
            if output_filename in existing_names:
                output_filename = f"{base_name}_{idx + 1}.jpg"

            output_path = os.path.join(output_folder, output_filename)

            convert_image_to_jpg(uploaded_file, output_path)
            successful_conversions.append(output_filename)

        except Exception as e:
            failed_conversions.append((uploaded_file.name, str(e)))

    progress_bar.empty()
    status_text.empty()

    if successful_conversions:
        st.markdown("### ✅ Conversion Results")

        st.markdown(f"""
            <div class="stats-container">
                <div class="stat-item">
                    <div class="stat-number">{len(successful_conversions)}</div>
                    <div class="stat-label">Successful</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len(failed_conversions)}</div>
                    <div class="stat-label">Failed</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("**✓ Successfully converted:**")
        for filename in successful_conversions:
            st.markdown(f"- {filename}")

        if failed_conversions:
            with st.expander("❌ Failed Conversions (Click to see details)"):
                for filename, error in failed_conversions:
                    st.error(f"**{filename}**: {error}")

        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(output_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, arcname=file)

            with open(zip_filename, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {len(successful_conversions)} Converted JPGs",
                    data=f.read(),
                    file_name=zip_filename,
                    mime="application/zip",
                    use_container_width=True
                )

            if len(successful_conversions) <= 5:
                st.markdown("**Or download individually:**")
                cols = st.columns(3)

                for i, filename in enumerate(successful_conversions):
                    file_path = os.path.join(output_folder, filename)
                    with open(file_path, "rb") as f:
                        with cols[i % 3]:
                            st.download_button(
                                label=filename,
                                data=f.read(),
                                file_name=filename,
                                mime="image/jpeg",
                                use_container_width=True,
                                key=f"download_{filename}_{i}"
                            )

        except Exception as e:
            st.error(f"Error creating download: {str(e)}")

else:
    st.markdown("""
        <div class="info-box">
            📸 No images selected yet. Upload one or more image files to get started!
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### 💡 How It Works
    1. Click "Browse files" above
    2. Select one or more image files
    3. PNG files are placed on a white background before conversion
    4. All files are converted to JPG format
    5. Download the converted files as a ZIP or individually

    ### ℹ️ Details
    - **PNG Handling**: PNG files are flattened onto a white background before conversion
    - **Transparency**: WEBP, GIF, and other transparent images are also placed on white
    - **TIF/TIFF Handling**: Multi-page TIFFs convert the first page; high bit-depth (16-bit) images are normalized to 8-bit
    - **Supported Input Formats**: JPG, JPEG, PNG, BMP, GIF, WEBP, TIF, TIFF
    - **Output Format**: JPEG (.jpg)
    - **Quality**: Saved at 95% JPEG quality
    """)

st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.85rem;">
        Last updated: {current_time_cst.strftime('%Y-%m-%d %H:%M:%S %Z')}
    </div>
""", unsafe_allow_html=True)
