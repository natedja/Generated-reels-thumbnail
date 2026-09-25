import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import google.generativeai as genai
import textwrap

st.set_page_config(page_title="Iotomagz Reels Generator", page_icon="🎬", layout="centered")

st.title("🎬 Iotomagz Reels Thumbnail Generator")
st.markdown("Generator otomatis menggunakan template greenscreen asli Anda.")

# --- SIDEBAR: KONFIGURASI AI ---
st.sidebar.header("🔑 Pengaturan AI (Gemini)")
api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)

# --- BAGIAN 1: INPUT GAMBAR ---
st.subheader("1. Upload Aset Gambar")
template_file = st.file_uploader("Upload Template (frame video ioto greenscreen.png):", type=["png", "jpg", "jpeg"])
bg_file = st.file_uploader("Upload Foto/Footage Konten (Background):", type=["png", "jpg", "jpeg"])

# --- BAGIAN 2: INPUT JUDUL ---
st.subheader("2. Teks Judul Highlight")
input_method = st.radio("Pilih Cara Input:", ["Input Manual", "AI Generate (Gemini)"])

headline = ""
if input_method == "Input Manual":
    headline = st.text_area("Tulis Judul Highlight:", "Lore impsum dolor\nLore impsum dolor")
else:
    topic = st.text_input("Topik (Cth: Motor sport 250cc paling irit 2026):")
    if st.button("✨ Generate Judul AI") and topic:
        if not api_key:
            st.warning("⚠️ Masukkan Gemini API Key di sidebar!")
        else:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Buatkan 1 judul menarik dan singkat untuk reels otomotif: '{topic}'. Maksimal 8 kata."
                response = model.generate_content(prompt)
                headline = response.text.strip().replace('"', '')
                st.success(f"Judul AI: **{headline}**")
            except Exception as e:
                st.error(f"Error AI: {e}")
                
    headline = st.text_area("Edit Judul:", headline)

# --- FUNGSI PROSES GAMBAR ---
def process_thumbnail(template_bytes, bg_bytes, text):
    width, height = 1080, 1920
    
    # 1. HAPUS GREENSCREEN DARI TEMPLATE
    template_img = Image.open(template_bytes).convert("RGBA")
    template_img = template_img.resize((width, height), Image.Resampling.LANCZOS)
    
    # Konversi ke array numpy untuk hapus warna hijau
    data = np.array(template_img)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Deteksi area hijau (Thresholding)
    # Angka ini cocok untuk warna hijau terang pada greenscreen
    green_mask = (g > 150) & (r < 100) & (b < 100) 
    data[:,:,3][green_mask] = 0 # Ubah area hijau jadi transparan (Alpha = 0)
    
    transparent_template = Image.fromarray(data)
    
    # 2. SIAPKAN BACKGROUND KONTEN
    if bg_bytes:
        bg_img = Image.open(bg_bytes).convert("RGBA")
        # Resize background agar pas layar
        bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
    else:
        # Jika belum ada foto, beri warna abu-abu gelap
        bg_img = Image.new("RGBA", (width, height), (30, 30, 30, 255))
        
    # 3. GABUNGKAN GAMBAR (Template di atas Background)
    bg_img.paste(transparent_template, (0, 0), transparent_template)
    
    # 4. TAMBAHKAN TEKS DI KOTAK HITAM
    draw = ImageDraw.Draw(bg_img)
    try:
        font = ImageFont.truetype("arialbd.ttf", 45) # Arial Bold jika ada
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", 45)
        except:
            font = ImageFont.load_default()
            
    # Wrap teks agar tidak keluar dari kotak hitam (maksimal ~32 karakter per baris)
    wrapped_text = textwrap.fill(text, width=32)
    
    # Koordinat teks (disesuaikan dengan posisi kotak hitam di gambar Anda)
    # Anda bisa mengatur ulang angka 120 (X) dan 1420 (Y) jika posisinya kurang pas
    draw.text((120, 1420), wrapped_text, fill=(255, 255, 255, 255), font=font, spacing=15)
    
    return bg_img.convert("RGB")

# --- TOMBOL RENDER ---
if st.button("🚀 Render Thumbnail", type="primary"):
    if not template_file:
        st.error("⚠️ Mohon upload gambar template greenscreen Anda (frame video ioto greenscreen.png) terlebih dahulu!")
    elif not headline:
        st.warning("⚠️ Mohon isi judul konten!")
    else:
        with st.spinner("Menghapus greenscreen dan merender gambar..."):
            result = process_thumbnail(template_file, bg_file, headline)
            
            st.image(result, caption="Hasil Akhir Thumbnail Reels")
            
            buf = io.BytesIO()
            result.save(buf, format="JPEG", quality=95)
            
            st.download_button(
                label="📥 Download Thumbnail Akhir (.JPG)",
                data=buf.getvalue(),
                file_name="thumbnail_iotomagz.jpg",
                mime="image/jpeg"
            )
