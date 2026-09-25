import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import google.generativeai as genai
import textwrap

st.set_page_config(page_title="Iotomagz Reels Generator", page_icon="🎬", layout="wide")

st.title("🎬 Iotomagz Reels Thumbnail Generator")
st.markdown("Upload gambar, generate judul, dan sesuaikan posisi teks Anda.")

# --- SIDEBAR: KONFIGURASI AI & POSISI TEKS ---
with st.sidebar:
    st.header("🔑 Pengaturan AI")
    api_key = st.text_input("Gemini API Key:", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        
    st.divider()
    
    st.header("🛠️ Sesuaikan Posisi Judul")
    st.markdown("Geser slider ini jika judul tidak pas di kotak hitam:")
    
    # SLIDER INTERAKTIF UNTUK TEKS
    text_x = st.slider("Geser Kiri - Kanan (X)", 0, 1080, 100)
    text_y = st.slider("Geser Atas - Bawah (Y)", 0, 1920, 1380)
    font_size = st.slider("Ukuran Font", 20, 100, 50)
    char_width = st.slider("Kapan teks pindah baris? (Lebar Teks)", 15, 60, 32)
    
    # Opsi Warna Teks
    text_color = st.color_picker("Pilih Warna Teks", "#FFFFFF") # Default Putih

# --- BAGIAN 1: INPUT GAMBAR ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Upload Aset")
    template_file = st.file_uploader("Upload Template Greenscreen:", type=["png", "jpg", "jpeg"])
with col2:
    st.subheader("Background")
    bg_file = st.file_uploader("Upload Foto/Footage (Background):", type=["png", "jpg", "jpeg"])

# --- BAGIAN 2: INPUT JUDUL ---
st.subheader("2. Teks Judul Highlight")
input_method = st.radio("Pilih Cara Input:", ["Input Manual", "AI Generate (Gemini)"])

headline = ""
if input_method == "Input Manual":
    headline = st.text_area("Tulis Judul Highlight:", "Ganti teks ini dengan\njudul konten Anda")
else:
    topic = st.text_input("Topik (Cth: Motor sport 250cc paling irit 2026):")
    if st.button("✨ Generate Judul AI") and topic:
        if not api_key:
            st.warning("⚠️ Masukkan Gemini API Key di sidebar sebelah kiri!")
        else:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Buatkan 1 judul menarik dan singkat untuk reels otomotif: '{topic}'. Maksimal 8-10 kata."
                response = model.generate_content(prompt)
                headline = response.text.strip().replace('"', '')
                st.success(f"Judul AI: **{headline}**")
            except Exception as e:
                st.error(f"Error AI: {e}")
                
    headline = st.text_area("Edit Judul:", headline)

# --- FUNGSI PROSES GAMBAR ---
def process_thumbnail(template_bytes, bg_bytes, text, x_pos, y_pos, f_size, c_width, color_hex):
    width, height = 1080, 1920
    
    # 1. Hapus Greenscreen (Proses numpy)
    template_img = Image.open(template_bytes).convert("RGBA")
    template_img = template_img.resize((width, height), Image.Resampling.LANCZOS)
    
    data = np.array(template_img)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    # Deteksi area hijau 
    green_mask = (g > 150) & (r < 100) & (b < 100) 
    data[:,:,3][green_mask] = 0
    transparent_template = Image.fromarray(data)
    
    # 2. Siapkan Background
    if bg_bytes:
        bg_img = Image.open(bg_bytes).convert("RGBA")
        bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
    else:
        bg_img = Image.new("RGBA", (width, height), (30, 30, 30, 255))
        
    # 3. Gabungkan
    bg_img.paste(transparent_template, (0, 0), transparent_template)
    
    # 4. Tulis Teks Dinamis
    draw = ImageDraw.Draw(bg_img)
    try:
        font = ImageFont.truetype("arialbd.ttf", f_size)
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", f_size)
        except:
            font = ImageFont.load_default()
            
    # Format agar pindah baris dan rata tengah
    wrapped_text = textwrap.fill(text, width=c_width)
    
    # Menggambar teks menggunakan parameter dari slider
    draw.text((x_pos, y_pos), wrapped_text, fill=color_hex, font=font, spacing=15, align="center")
    
    return bg_img.convert("RGB")

# --- TOMBOL RENDER ---
if st.button("🚀 Render & Pratinjau Thumbnail", type="primary"):
    if not template_file:
        st.error("⚠️ Mohon upload gambar template Anda (frame video ioto greenscreen.png) terlebih dahulu!")
    elif not headline:
        st.warning("⚠️ Mohon isi judul konten!")
    else:
        with st.spinner("Menyatukan gambar..."):
            # Panggil fungsi dengan mengambil nilai dari slider sidebar
            result = process_thumbnail(template_file, bg_file, headline, text_x, text_y, font_size, char_width, text_color)
            
            st.image(result, caption="Pratinjau Hasil (Gunakan slider di kiri jika posisi teks belum pas)")
            
            buf = io.BytesIO()
            result.save(buf, format="JPEG", quality=95)
            
            st.download_button(
                label="📥 Download Thumbnail Akhir (.JPG)",
                data=buf.getvalue(),
                file_name="thumbnail_iotomagz.jpg",
                mime="image/jpeg"
            )
