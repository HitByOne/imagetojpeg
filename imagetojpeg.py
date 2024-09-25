import streamlit as st
from PIL import Image
import os
import zipfile

# Title of the app
st.title("Image to JPG Converter")

# File uploader to select image files
uploaded_files = st.file_uploader("Choose image files", type=["jpg", "jpeg", "png", "bmp", "gif"], accept_multiple_files=True)

if uploaded_files:
    # Create a temporary directory to save converted files
    output_folder = "converted_files"
    os.makedirs(output_folder, exist_ok=True)

    # Process each uploaded file
    for uploaded_file in uploaded_files:
        # Open the uploaded image file
        with Image.open(uploaded_file) as img:
            # Define the output path
            output_path = os.path.join(output_folder, f"{os.path.splitext(uploaded_file.name)[0]}.jpg")
            # Convert to JPG and save
            img.convert("RGB").save(output_path, "JPEG")
            st.success(f"Converted {uploaded_file.name} to JPG.")

    # Create a zip file of the converted files
    zip_filename = "converted_images.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(output_folder):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    # Provide a download link for the zip file
    with open(zip_filename, "rb") as f:
        st.download_button("Download ZIP of Converted Files", f, file_name=zip_filename)

# Show a message if no files are uploaded
if not uploaded_files:
    st.info("Please upload image files to convert.")
