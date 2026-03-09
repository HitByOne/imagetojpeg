import streamlit as st
from PIL import Image
import os
import zipfile
import shutil
import datetime
import pytz
from io import BytesIO
import traceback

# Page configuration
st.set_page_config(
    page_title="Image to JPG Converter",
    page_icon="🖼️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
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
    
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        color: #155724;
        margin-bottom: 0.5rem;
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

# Title and subtitle
st.markdown("# 🖼️ Image to JPG Converter")
st.markdown("""
    <div class="subtitle">
        Convert your images to JPG format instantly
    </div>
""", unsafe_allow_html=True)

# Set the timezone to CST
cst_timezone = pytz.timezone('America/Chicago')
current_time_cst = datetime.datetime.now(cst_timezone)

# Output folder setup
output_folder = "converted_files"
zip_filename = "converted_images.zip"

# Clean up previous session files
def cleanup_files():
    """Clean up any existing converted files from previous sessions"""
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

# Initialize session state
if "conversion_complete" not in st.session_state:
    st.session_state.conversion_complete = False
    st.session_state.converted_count = 0
    st.session_state.error_messages = []

# File uploader
st.markdown("### 📁 Select Images to Convert")
uploaded_files = st.file_uploader(
    "Choose image files (JPG, PNG, BMP, GIF)",
    type=["jpg", "jpeg", "png", "bmp", "gif"],
    accept_multiple_files=True,
    help="Select one or more image files to convert to JPG format"
)

if uploaded_files:
    # Clean up before starting new conversion
    cleanup_files()
    
    # Create output directory
    os.makedirs(output_folder, exist_ok=True)
    
    # Track results
    successful_conversions = []
    failed_conversions = []
    
    st.markdown("### ⚙️ Converting Images...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process each uploaded file
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            # Update progress
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing: {uploaded_file.name}")
            
            # Open and convert the image
            with Image.open(uploaded_file) as img:
                # Handle RGBA images (transparent PNGs)
                if img.mode in ("RGBA", "LA", "P"):
                    # Create a white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                else:
                    img = img.convert("RGB")
                
                # Define output path
                output_filename = f"{os.path.splitext(uploaded_file.name)[0]}.jpg"
                output_path = os.path.join(output_folder, output_filename)
                
                # Save as JPG with quality settings
                img.save(output_path, "JPEG", quality=95, optimize=True)
                successful_conversions.append(output_filename)
                
        except Exception as e:
            failed_conversions.append((uploaded_file.name, str(e)))
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    if successful_conversions:
        st.markdown("### ✅ Conversion Results")
        
        # Statistics
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
        
        # Show successful conversions
        if successful_conversions:
            st.markdown("**✓ Successfully converted:**")
            for filename in successful_conversions:
                st.markdown(f"- {filename}")
        
        # Show failed conversions with error details
        if failed_conversions:
            with st.expander("❌ Failed Conversions (Click to see details)"):
                for filename, error in failed_conversions:
                    st.error(f"**{filename}**: {error}")
        
        # Create zip file of successful conversions
        if successful_conversions:
            try:
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(output_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, arcname=file)
                
                # Download button
                with open(zip_filename, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {len(successful_conversions)} Converted JPGs",
                        data=f.read(),
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )
                
                # Also offer individual downloads
                if len(successful_conversions) <= 5:
                    st.markdown("**Or download individually:**")
                    col1, col2, col3 = st.columns(3)
                    col_idx = 0
                    
                    for filename in successful_conversions:
                        file_path = os.path.join(output_folder, filename)
                        with open(file_path, "rb") as f:
                            col = [col1, col2, col3][col_idx % 3]
                            with col:
                                st.download_button(
                                    label=filename,
                                    data=f.read(),
                                    file_name=filename,
                                    mime="image/jpeg",
                                    use_container_width=True
                                )
                            col_idx += 1
                
            except Exception as e:
                st.error(f"Error creating download: {str(e)}")

else:
    # Show info message when no files are uploaded
    st.markdown("""
        <div class="info-box">
            📸 No images selected yet. Upload one or more image files to get started!
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 💡 How It Works
    1. Click "Browse files" above
    2. Select one or more image files (JPG, PNG, BMP, or GIF)
    3. Your images will be converted to JPG format
    4. Download the converted files as a ZIP or individually
    
    ### ℹ️ Details
    - **Quality**: Saved at 95% JPEG quality for optimal file size and clarity
    - **Transparency**: PNG images with transparency will be placed on a white background
    - **Safe**: All files are processed and deleted after download
    """)

# Footer with timestamp
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.85rem;">
        Last updated: {current_time_cst.strftime('%Y-%m-%d %H:%M:%S')} CST
    </div>
""", unsafe_allow_html=True)
