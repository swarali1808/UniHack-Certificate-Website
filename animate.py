import streamlit as st
import io
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import pandas as pd
import os
import base64

# --- CONFIGURATION & ASSETS ---
def get_base64_of_bin_file(bin_file):
    """Encodes a local file to base64 for use in CSS."""
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# Load Assets
logo_path = "Logo.jpg"
logo = Image.open(logo_path) if os.path.exists(logo_path) else None
font_path = os.path.abspath("Oregano-Regular.ttf")

# Generate Background CSS
bg_base64 = get_base64_of_bin_file("bg.jpg")
bg_style = f'background-image: url("data:image/jpg;base64,{bg_base64}"); background-size: cover; background-attachment: fixed;' if bg_base64 else "background-color: #f0f2f6;"

st.set_page_config(page_title="DJS NSS Event", page_icon=logo)

# --- STYLING ---
custom_css = f"""
<style>
    .stApp {{
        {bg_style}
    }}
    
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.9);
        padding: 40px !important;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-top: 50px;
        max-width: 800px;
    }}

    .custom-title {{
        color: #1e293b;
        font-size: 45px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 30px;
    }}

    /* Input Field: White BG, Black Text */
    .stTextInput input {{
        background-color: white !important;
        color: black !important;
        font-size: 18px !important;
        padding: 12px !important;
        text-align: center !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }}

    /* Selectbox Field: White BG, Black Text */
    div[data-baseweb="select"] > div {{
        background-color: white !important;
        color: black !important;
        border-radius: 10px !important;
    }}

    /* Selectbox selected text color */
    div[data-testid="stSelectbox"] p {{
        color: black !important;
    }}
    
    /* Dropdown menu items */
    ul[role="listbox"] li {{
        background-color: white !important;
        color: black !important;
    }}

    /* GLOBAL BUTTON STYLING (Generate & Download) */
    div.stButton > button, div.stDownloadButton > button {{
        background-color: #167274 !important;
        color: white !important;
        width: 100%;
        height: 50px;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 18px !important;
        transition: 0.3s all ease-in-out !important;
    }}

    div.stButton > button:hover, div.stDownloadButton > button:hover {{
        background-color: #45c6ae !important;
        color: white !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border: none !important;
    }}
    
    /* Ensure text remains white even when clicked/active */
    div.stButton > button:active, div.stDownloadButton > button:active {{
        color: white !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- APP DATA ---
EVENTS = {"UniHacks 2026": "unihacks"}
POSITIONS = {"unihacks": {"name": (0.5, 0.51)}}

# --- LOGIC ---
def get_attendee_status(name, event_display):
    event_key = EVENTS[event_display]
    csv_path = f"attendance/{event_key}.csv"
    try:
        if not os.path.exists(csv_path): return None
        df = pd.read_csv(csv_path)
        name_col = [c for c in df.columns if c.strip().lower() == "name"][0]
        df["Name_norm"] = df[name_col].astype(str).str.strip().str.lower()
        return not df[df["Name_norm"] == name.strip().lower()].empty
    except: return None

def overlay_name_on_template(name, event_display):
    event_key = EVENTS[event_display]
    template_path = f"templates/{event_key}.png"
    if not os.path.exists(template_path): return None
    
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    pos = POSITIONS.get(event_key, {}).get("name", (0.5, 0.5))
    
    try:
        font = ImageFont.truetype(font_path, 150)
    except:
        font = ImageFont.load_default()

    # Name Color remains #092b2c
    draw.text((int(w*pos[0]), int(h*pos[1])), name, fill="#092b2c", anchor="mm", font=font)
    return img

def generate_pdf(img_result):
    img_buf = io.BytesIO()
    img_result.save(img_buf, format="PNG")
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=(img_result.width, img_result.height))
    c.drawImage(ImageReader(img_buf), 0, 0, width=img_result.width, height=img_result.height)
    c.showPage()
    c.save()
    pdf_buf.seek(0)
    return pdf_buf

# --- MAIN UI ---
def main():
    col1, col2 = st.columns([1, 4])
    with col1:
        if logo: st.image(logo, width=100)
    with col2:
        st.markdown('<div class="custom-title">DJS UniCode</div>', unsafe_allow_html=True)
    
    user_input = st.text_input("Enter your full name:", placeholder="John Doe").strip().title()
    event_display = st.selectbox("Select Event", list(EVENTS.keys()))
    
    if st.button("Generate Certificate"):
        if user_input:
            if not get_attendee_status(user_input, event_display):
                st.warning(f"⚠️ Name not found in the list.")
                return
            
            img_result = overlay_name_on_template(user_input, event_display)
            if img_result:
                st.image(img_result, caption="Preview", use_container_width=True)
                pdf_file = generate_pdf(img_result)
                
                # Download Button (will now match Generate button style)
                st.download_button(
                    label="Download Certificate (PDF)",
                    data=pdf_file.getvalue(),
                    file_name=f"{user_input}.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("⚠️ Please enter your name.")

if __name__ == "__main__":
    main()