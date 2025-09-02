import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import os
from streamlit_drawable_canvas import st_canvas
import tempfile

st.set_page_config(page_title="Advanced Certificate Generator", layout="wide")

st.title("🎖️ Advanced Certificate Generator")

# --- Step 1: Upload certificate template ---
st.sidebar.header("Step 1: Upload Certificate Template")
template_file = st.sidebar.file_uploader("Upload a certificate template (PNG/JPG)", type=["png", "jpg", "jpeg"])

# --- Step 2: Upload data file ---
st.sidebar.header("Step 2: Upload CSV/Excel File")
data_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
data_df = None
if data_file:
    try:
        if data_file.name.endswith(".csv"):
            data_df = pd.read_csv(data_file)
        else:
            data_df = pd.read_excel(data_file)
        st.sidebar.success(f"Data loaded! Columns: {', '.join(data_df.columns)}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# --- Step 3: Font Upload ---
st.sidebar.header("Step 3: Upload Custom Font (Optional)")
font_file = st.sidebar.file_uploader("Upload .ttf font", type=["ttf"])
default_font_path = None
if not font_file:
    st.sidebar.info("Using default PIL font")

# --- Step 4: Select columns and configure text boxes ---
st.sidebar.header("Step 4: Configure Text Boxes")
text_boxes_config = []

if data_df is not None:
    num_text_boxes = st.sidebar.slider("Number of text boxes to configure (per row)", 1, 5, 1)
    
    for i in range(num_text_boxes):
        st.sidebar.subheader(f"Text Box {i+1}")
        column_name = st.sidebar.selectbox(f"Select column for Text Box {i+1}", data_df.columns, key=f"col_{i}")
        prefix = st.sidebar.text_input(f"Prefix for {column_name}", key=f"prefix_{i}")
        suffix = st.sidebar.text_input(f"Suffix for {column_name}", key=f"suffix_{i}")
        font_size = st.sidebar.number_input(f"Font size for {column_name}", min_value=10, max_value=200, value=40, key=f"size_{i}")
        font_color = st.sidebar.color_picker(f"Font color for {column_name}", "#000000", key=f"color_{i}")
        bold = st.sidebar.checkbox(f"Bold", key=f"bold_{i}")
        italic = st.sidebar.checkbox(f"Italic", key=f"italic_{i}")
        
        text_boxes_config.append({
            "column": column_name,
            "prefix": prefix,
            "suffix": suffix,
            "font_size": font_size,
            "font_color": font_color,
            "bold": bold,
            "italic": italic,
            "x": 100,  # default position
            "y": 100
        })

# --- Step 5: Drag-and-drop positioning ---
st.header("📌 Position Text Boxes on Certificate")
if template_file and text_boxes_config:
    image = Image.open(template_file).convert("RGBA")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=1,
        background_image=image,
        update_streamlit=True,
        height=image.height,
        width=image.width,
        drawing_mode="text",
        key="canvas",
        display_toolbar=True
    )
    
    # Show preview of text boxes
    preview_img = image.copy()
    draw = ImageDraw.Draw(preview_img)
    
    def load_font(size):
        try:
            if font_file:
                return ImageFont.truetype(font_file, size)
            else:
                return ImageFont.load_default()
        except:
            return ImageFont.load_default()
    
    for tb in text_boxes_config:
        text = f"{tb['prefix']}{data_df.iloc[0][tb['column']]}{tb['suffix']}"
        font = load_font(tb['font_size'])
        draw.text((tb["x"], tb["y"]), text, fill=tb["font_color"], font=font)
    
    st.image(preview_img, caption="Preview of first certificate")

# --- Step 6: Generate Certificates ---
st.header("🎉 Generate Certificates")
if st.button("Generate All Certificates") and data_df is not None and template_file and text_boxes_config:
    temp_zip = BytesIO()
    with zipfile.ZipFile(temp_zip, mode="w") as zf:
        for idx, row in data_df.iterrows():
            cert_img = Image.open(template_file).convert("RGBA")
            draw = ImageDraw.Draw(cert_img)
            for tb in text_boxes_config:
                text = f"{tb['prefix']}{row[tb['column']]}{tb['suffix']}"
                font = load_font(tb["font_size"])
                draw.text((tb["x"], tb["y"]), text, fill=tb["font_color"], font=font)
            
            # Save image to BytesIO
            img_bytes = BytesIO()
            cert_img.save(img_bytes, format="PNG")
            zf.writestr(f"certificate_{idx+1}.png", img_bytes.getvalue())
    
    temp_zip.seek(0)
    st.download_button("Download All Certificates (ZIP)", data=temp_zip, file_name="certificates.zip")

st.sidebar.markdown("---")
st.sidebar.info("This app uses `streamlit_drawable_canvas` to position text boxes. Use drag-and-drop to move text, then generate certificates.")
