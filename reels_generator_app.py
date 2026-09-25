import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import google.generativeai as genai

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Generator Thumbnail Reels", page_icon="🎬", layout="centered")

st.title("🎬 Generator Thumbnail Reels Instagram")
st.markdown("Aplikasi web interaktif untuk membuat thumbnail Reels berukuran vertikal (1080x1920) dengan gaya template kustom dan integrasi AI (Gemini).")

# Sidebar untuk Konfigurasi API AI
st.sidebar.header("🔑 Pengaturan AI (Gemini API)")
api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password", help="Dapatkan API key gratis melalui Google AI Studio")

if api_key:
    genai.configure(api_key=api_key)

# Input Pengguna
st.subheader("1. Judul / Highlight Konten")
input_method = st.radio("Pilih Cara Input Judul:", ["Input Teks Manual", "Generate Otomatis dengan AI (Gemini)"])

headline = ""
if input_method == "Input Teks Manual":
    headline = st.text_area("Tulis Judul Highlight:", "Lore impsum dolor Lore impsum dolor dolor Lore impsum dolor")
else:
    topic = st.text_input("Masukkan Topik / Ide Konten (Cth: Review mobil listrik terbaru di GIIAS 2026):")
    if st.button("✨ Generate Judul dengan AI") and topic:
        if not api_key:
            st.warning("⚠️ Mohon masukkan Gemini API Key di sidebar terlebih dahulu!")
        else:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Buatkan 1 judul highlight yang menarik, catchy, dan singkat untuk reels instagram dengan topik: '{topic}'. Batasi maksimal 8-10 kata agar pas di dalam kotak thumbnail, dan buat agar memancing rasa penasaran."
                response = model.generate_content(prompt)
                headline = response.text.strip().replace('"', '')
                st.success(f"Berhasil dibuat: **{headline}**")
            except Exception as e:
                st.error(f"Gagal generate judul: {e}")

    headline = st.text_area("Edit/Sesuaikan Judul:", headline)

st.subheader("2. Upload Background Foto / Footage")
uploaded_file = st.file_uploader("Pilih file gambar untuk background:", type=["jpg", "jpeg", "png"])

# Fungsi Pembuat Thumbnail
def generate_thumbnail(bg_image, title_text):
    width, height = 1080, 1920
    
    # 1. Base Image (Background)
    if bg_image:
        base = Image.open(bg_image).convert("RGBA")
        base = base.resize((width, height), Image.Resampling.LANCZOS)
    else:
        # Default hijau jika tidak ada foto (greenscreen)
        base = Image.new("RGBA", (width, height), (34, 139, 34, 255))
        
    # 2. Layer Overlay / Elemen Grafis
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Kotak Teks Hitam di Bawah (Polygon menyerupai template contoh)
    box_points = [(70, 1200), (1010, 1200), (1010, 1680), (40, 1780)]
    draw.polygon(box_points, fill=(0, 0, 0, 225)) # Hitam semi-transparan
    
    # Badge Logo di Kanan Atas
    logo_box = [(620, 50), (1030, 150), (1030, 210), (660, 210)]
    draw.polygon(logo_box, fill=(0, 0, 0, 235))
    
    # Load Font (fallback jika font sistem tidak ada)
    try:
        font_title = ImageFont.truetype("arial.ttf", 55)
        font_logo = ImageFont.truetype("arial.ttf", 45)
    except IOError:
        font_title = ImageFont.load_default()
        font_logo = ImageFont.load_default()
        
    # Tulis Teks Logo
    draw.text((680, 80), "iotomagz !", fill=(255, 255, 255, 255), font=font_logo)
    
    # Tulis Judul Highlight
    margin_x, margin_y = 105, 1260
    draw.text((margin_x, margin_y), title_text, fill=(255, 255, 255, 255), font=font_title, spacing=15)
    
    # Gabungkan layer
    final_image = Image.alpha_composite(base, overlay)
    return final_image.convert("RGB")

if st.button("🚀 Render Thumbnail Reels", type="primary"):
    if not headline:
        st.warning("Mohon isi judul highlight terlebih dahulu!")
    else:
        with st.spinner("Sedang memproses gambar..."):
            result_img = generate_thumbnail(uploaded_file, headline)
            
            # Tampilkan hasil di UI
            st.image(result_img, caption="Pratinjau Thumbnail Reels Instagram", use_column_width=True)
            
            # Siapkan data untuk tombol download
            buf = io.BytesIO()
            result_img.save(buf, format="JPEG", quality=95)
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 Download Thumbnail (.JPG)",
                data=byte_im,
                file_name="thumbnail_reels.jpg",
                mime="image/jpeg"
            )
