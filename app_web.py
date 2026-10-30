import streamlit as st
from datetime import datetime
import pandas as pd
import qrcode
from io import BytesIO
import sqlite3

# --- 1. INISIALISASI DATABASE & SESSION STATE ---
# (Kode init_db, seed_produk_awal Anda di sini)


if 'logged_in' not in st.session_state:
  st.session_state['logged_in'] = False


# --- 2. CEK LOGIN (JIKA BELUM LOGIN, TAMPILKAN FORM & STOP) ---
if not st.session_state['logged_in']:


  # Membuat 3 kolom untuk menengahkan tampilan
  col1, col2, col3 = st.columns([1, 2, 1])

  with col2:
    # Tampilkan Logo di dalam kolom tengah
    st.image('rs_py.jpg', width=200)

  st.title('🔒 Login Kasir - Rangers Store')

  with st.form('login_form'):
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    submit = st.form_submit_button('Login')

    if submit:
      if username == 'redflag' and password == 'rangers123':
        st.session_state['logged_in'] = True
        st.success('Login Berhasil!')
        st.rerun()
      else:
        st.error('Username atau Password salah!')

  # PERINTAH INI SANGAT PENTING:
  # Menghentikan jalannya aplikasi agar kode di bawahnya tidak ikut tampil sebelum login!
  st.stop()


# --- 3. KODE UTAMA APLIKASI (Hanya jalan kalau sudah login) ---
# Tombol Logout di sidebar
st.sidebar.write('---')
if st.sidebar.button('🚪 Logout'):
  st.session_state['logged_in'] = False
  st.rerun()

# Seluruh kode POS utama Anda (Navigasi, Katalog, Keranjang, dll) ada di bawah ini:
st.title('Rangers Store POS')
# ... dan seterusnya ...


# --- Fungsionalitas Database SQLite ---
def init_db():
    conn = sqlite3.connect('toko.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produk (
            id TEXT PRIMARY KEY,
            nama TEXT,
            kategori TEXT,
            harga REAL,
            stok INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id_transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            total REAL,
            detail TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
# -------------------------------------
def seed_produk_awal():
  conn = sqlite3.connect('toko.db')
  cursor = conn.cursor()

  
  # Cek apakah tabel produk masih kosong
  cursor.execute('SELECT COUNT(*) FROM produk')
  count = cursor.fetchone()[0]

  if count == 0:
    produk_awal = [
        ('P001', 'Jersey Home Rangers', 'Jersey', 150000, 10),
        ('P002', 'Jersey Away Rangers', 'Jersey', 150000, 8),
        ('P003', 'Tas Ransel Laptop 15 Inch', 'Aksesoris', 175000, 12),
        ('P004', 'Smartwatch Fitness', 'Elektronik', 450000, 3),
        ('P005', 'Topi Baseball Polos', 'Aksesoris', 45000, 20),
    ]
    cursor.executemany(
        'INSERT INTO produk (id, nama, kategori, harga, stok) VALUES (?, ?,'
        ' ?, ?, ?)',
        produk_awal,
    )
    conn.commit()

  conn.close()


seed_produk_awal()

# Ambil data produk dari database SQLite
conn = sqlite3.connect('toko.db')
df_produk = pd.read_sql('SELECT * FROM produk', conn)
conn.close()


# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN & CUSTOM CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Rangers Store - Point of Sale",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-title h1 {
        margin: 0;
        font-weight: 700;
        font-size: 2.2rem;
    }
    .main-title p {
        margin: 5px 0 0 0;
        opacity: 0.9;
    }
    .receipt-box {
        background-color: #fff9e6;
        border: 2px dashed #d4a373;
        border-radius: 8px;
        padding: 20px;
        font-family: 'Courier New', Courier, monospace;
        color: #333;
    }
    .qris-box {
        background-color: #ffffff;
        border: 2px solid #2a5298;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .badge-stock {
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-in-stock { background-color: #d4edda; color: #155724; }
    .badge-low-stock { background-color: #fff3cd; color: #856404; }
    .badge-out-stock { background-color: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. INISIALISASI SESSION STATE
# ---------------------------------------------------------
if "produk_toko" not in st.session_state:
    st.session_state.produk_toko = [
        {"id": "P001", "nama": "Kemeja Flanel Casual", "kategori": "Pakaian", "harga_jual": 125000, "stok": 15},
        {"id": "P002", "nama": "Sepatu Sneakers Running", "kategori": "Sepatu", "harga_jual": 299000, "stok": 8},
        {"id": "P003", "nama": "Tas Ransel Laptop 15 Inch", "kategori": "Aksesori", "harga_jual": 175000, "stok": 12},
        {"id": "P004", "nama": "Smartwatch Fitness", "kategori": "Elektronik", "harga_jual": 450000, "stok": 3},
        {"id": "P005", "nama": "Topi Baseball Polos", "kategori": "Aksesori", "harga_jual": 45000, "stok": 20}
    ]

if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

if "riwayat" not in st.session_state:
    st.session_state.riwayat = []

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None

def fmt_rp(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# Fungsi helper membuat gambar QR secara lokal (di dalam memori python)
def generate_qris_image(data_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# 3. HEADER UTAMA
# ---------------------------------------------------------
st.markdown("""
<div class="main-title">
    <h1>🛍️ RANGERS STORE POS</h1>
    <p>Sistem Kasir & Management Inventaris Modern (Support QRIS Lokal)</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3144/3144456.png", width=90)
    st.title("Menu Utama")
    menu = st.radio(
        "Pilih Navigasi:",
        ["🛒 Transaksi Kasir", "📦 Kelola Stok Produk", "📊 Laporan Penjualan"],
        index=0
    )
    st.markdown("---")
    st.caption("📌 **Ringkasan Cepat**")
    total_stok = sum(p["stok"] for p in st.session_state.produk_toko)
    st.write(f"• Total Jenis Produk: **{len(st.session_state.produk_toko)}**")
    st.write(f"• Total Unit Stok: **{total_stok}**")
    st.write(f"• Transaksi Hari Ini: **{len(st.session_state.riwayat)}**")
    st.markdown("---")
    st.caption("© 2026 Rangers Store Systems")

# ================= MENU 1: KASIR =================
if menu == "🛒 Transaksi Kasir":
    col_left, col_right = st.columns([1.6, 1.4])
    
    with col_left:
        st.subheader("🛍️ Katalog Produk")
        c_search, c_kat = st.columns([2, 1])
        with c_search:
            search_query = st.text_input("🔍 Cari produk...", "", placeholder="Ketik nama produk...")
        with c_kat:
            kategori_list = ["Semua"] + list(set(p["kategori"] for p in st.session_state.produk_toko))
            kat_filter = st.selectbox("Kategori", kategori_list)
        
        st.markdown("---")
        
        filtered_products = [
            p for p in st.session_state.produk_toko
            if (search_query.lower() in p["nama"].lower() or search_query.lower() in p["id"].lower())
            and (kat_filter == "Semua" or p["kategori"] == kat_filter)
        ]
        
        if not filtered_products:
            st.warning("Produk tidak ditemukan.")
        else:
            for p in filtered_products:
                with st.container():
                    st.markdown(f"##### **{p['nama']}** `[{p['id']}]`")
                    c1, c2, c3 = st.columns([2, 1.5, 1])
                    
                    with c1:
                        st.caption(f"📁 {p['kategori']} | **{fmt_rp(p['harga_jual'])}**")
                    with c2:
                        if p['stok'] == 0:
                            st.markdown("<span class='badge-stock badge-out-stock'>Habis</span>", unsafe_allow_html=True)
                        elif p['stok'] <= 5:
                            st.markdown(f"<span class='badge-stock badge-low-stock'>Stok: {p['stok']}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span class='badge-stock badge-in-stock'>Stok: {p['stok']}</span>", unsafe_allow_html=True)
                    with c3:
                        if st.button("➕ Tambah", key=f"btn_add_{p['id']}", disabled=(p['stok'] == 0)):
                            found = False
                            for item in st.session_state.keranjang:
                                if item["id"] == p["id"]:
                                    if item["qty"] < p["stok"]:
                                        item["qty"] += 1
                                        item["subtotal"] = item["qty"] * item["harga"]
                                        found = True
                                        st.toast(f"✅ {p['nama']} ditambah (+1)")
                                    else:
                                        st.warning("Mencapai batas stok!")
                                        found = True
                                    break
                            if not found:
                                st.session_state.keranjang.append({
                                    "id": p["id"],
                                    "nama": p["nama"],
                                    "harga": p["harga_jual"],
                                    "qty": 1,
                                    "subtotal": p["harga_jual"]
                                })
                                st.toast(f"✅ {p['nama']} ditambahkan ke keranjang")
                            st.rerun()
                    st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

    with col_right:
        st.subheader("🛒 Keranjang Belanja")
        
        if not st.session_state.keranjang:
            st.info("Keranjang belanja masih kosong. Pilih produk di sebelah kiri.")
        else:
            total_belanja = 0
            for idx, item in enumerate(st.session_state.keranjang):
                c_item_nama, c_item_qty, c_item_sub, c_item_del = st.columns([2.5, 1.5, 1.5, 0.5])
                
                with c_item_nama:
                    st.write(f"**{item['nama']}**")
                    st.caption(f"@ {fmt_rp(item['harga'])}")
                
                with c_item_qty:
                    stok_max = next(p["stok"] for p in st.session_state.produk_toko if p["id"] == item["id"])
                    new_qty = st.number_input(
                        "Qty", min_value=1, max_value=stok_max, value=item["qty"], 
                        key=f"qty_{item['id']}_{idx}", label_visibility="collapsed"
                    )
                    if new_qty != item["qty"]:
                        item["qty"] = new_qty
                        item["subtotal"] = item["qty"] * item["harga"]
                        st.rerun()

                with c_item_sub:
                    st.write(f"**{fmt_rp(item['subtotal'])}**")
                    
                with c_item_del:
                    if st.button("❌", key=f"del_{item['id']}_{idx}"):
                        st.session_state.keranjang.pop(idx)
                        st.rerun()
                
                total_belanja += item["subtotal"]
                st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
            
            st.markdown(f"### 💳 Total Tagihan: **{fmt_rp(total_belanja)}**")
            
            # Pilihan Metode Pembayaran (Tunai vs QRIS)
            st.markdown("#### 💳 Pilih Metode Pembayaran")
            metode_bayar = st.radio("Metode:", ["💵 Tunai (Cash)", "📱 QRIS (GoPay/OVO/BCA/ShopeePay dll)"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("---")
            
            if metode_bayar == "💵 Tunai (Cash)":
                bayar = st.number_input("Jumlah Uang Diterima (Rp)", min_value=0, step=5000, value=int(total_belanja))
                kembalian = bayar - total_belanja
                
                if kembalian >= 0:
                    st.success(f"Kembalian: **{fmt_rp(kembalian)}**")
                else:
                    st.error(f"Uang kurang: **{fmt_rp(abs(kembalian))}**")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Selesaikan Transaksi", use_container_width=True, disabled=(kembalian < 0)):
                        for item in st.session_state.keranjang:
                            for p in st.session_state.produk_toko:
                                if p["id"] == item["id"]:
                                    p["stok"] -= item["qty"]
                        
                        trans_id = f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        waktu_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        st.session_state.riwayat.append({
                            "id_transaksi": trans_id, "waktu": waktu_str, "total": total_belanja,
                            "metode": "Tunai", "bayar": bayar, "kembali": kembalian, "items": st.session_state.keranjang.copy()
                        })
                        st.session_state.last_receipt = {
                            "id": trans_id, "waktu": waktu_str, "items": st.session_state.keranjang.copy(),
                            "total": total_belanja, "metode": "Tunai", "bayar": bayar, "kembali": kembalian
                        }
                        st.session_state.keranjang = []
                        st.success("🎉 Transaksi Tunai Berhasil!")
                        st.rerun()

                with c_btn2:
                    if st.button("🗑️ Batal", use_container_width=True):
                        st.session_state.keranjang = []
                        st.rerun()

            else:
                # BAGIAN QRIS MENGGUNAKAN GENERATOR LOKAL
                # BAGIAN QRIS MENGGUNAKAN QRIS ASLI TOKO ANDA
                st.markdown("""
                <div class="qris-box">
                    <h3 style="color: #1e3c72; margin-bottom: 5px;">Scan QRIS untuk Membayar</h3>
                    <p style="font-size: 0.85rem; color: #666;">AKEWW, GAMING (Mendukung semua m-Banking & E-Wallet)</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Menampilkan QRIS Asli (qris_toko.jpg)
                col_q1, col_q2, col_q3 = st.columns([1, 2, 1])
                with col_q2:
                    st.image("qr_toko.jpg", width=220, caption=f"Total: {fmt_rp(total_belanja)}")
                
                st.write("")
                c_qris1, c_qris2 = st.columns(2)
                with c_qris1:
                    if st.button("✅ Konfirmasi Pembayaran QRIS Lunas", use_container_width=True):
                        for item in st.session_state.keranjang:
                            for p in st.session_state.produk_toko:
                                if p["id"] == item["id"]:
                                    p["stok"] -= item["qty"]
                        
                        trans_id = f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        waktu_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        st.session_state.riwayat.append({
                            "id_transaksi": trans_id, "waktu": waktu_str, "total": total_belanja,
                            "metode": "QRIS", "bayar": total_belanja, "kembali": 0, "items": st.session_state.keranjang.copy()
                        })
                        st.session_state.last_receipt = {
                            "id": trans_id, "waktu": waktu_str, "items": st.session_state.keranjang.copy(),
                            "total": total_belanja, "metode": "QRIS", "bayar": total_belanja, "kembali": 0
                        }
                        st.session_state.keranjang = []
                        st.success("🎉 Pembayaran QRIS Berhasil Diterima!")
                        st.rerun()
                with c_qris2:
                    if st.button("🗑️ Batal / Ganti", use_container_width=True):
                        st.session_state.keranjang = []
                        st.rerun()
# ================= MENU 2: KELOLA STOK =================
elif menu == "📦 Kelola Stok Produk":
    st.subheader("📦 Manajemen Inventaris Produk")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Jenis Produk", len(st.session_state.produk_toko))
    m2.metric("Total Unit Stok Tersedia", sum(p['stok'] for p in st.session_state.produk_toko))
    m3.metric("Produk Stok Menipis (<=5)", sum(1 for p in st.session_state.produk_toko if p['stok'] <= 5))
    
    st.markdown("---")
    tab1, tab2 = st.tabs(["📋 Daftar Produk Saat Ini", "➕ Tambah / Edit Produk Baru"])
    
    with tab1:
        df_produk = pd.DataFrame(st.session_state.produk_toko)
        df_produk.columns = ["ID", "Nama Produk", "Kategori", "Harga Jual (Rp)", "Stok Tersedia"]
        df_display = df_produk.copy()
        df_display["Harga Jual (Rp)"] = df_display["Harga Jual (Rp)"].apply(fmt_rp)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("#### ⚡ Quick Update Stok")
        col_sel, col_val, col_act = st.columns([2, 1, 1])
        with col_sel:
            p_selected = st.selectbox("Pilih Produk", [f"{p['id']} - {p['nama']}" for p in st.session_state.produk_toko])
        with col_val:
            stok_adj = st.number_input("Jumlah Adjust (+/-)", value=5, step=1)
        with col_act:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Update Stok", use_container_width=True):
                target_id = p_selected.split(" - ")[0]
                for p in st.session_state.produk_toko:
                    if p["id"] == target_id:
                        p["stok"] = max(0, p["stok"] + stok_adj)
                        st.success(f"Stok {p['nama']} diperbarui menjadi {p['stok']}")
                        st.rerun()
                        
    with tab2:
        st.write("##### **Form Tambah Produk Baru**")
        with st.form("form_tambah_produk", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nama_baru = st.text_input("Nama Produk", placeholder="Contoh: Jaket Denim Vintage")
                kat_baru = st.selectbox("Kategori Produk", ["Pakaian", "Sepatu", "Aksesori", "Elektronik", "Lainnya"])
            with col_f2:
                harga_baru = st.number_input("Harga Jual (Rp)", min_value=0, step=5000, value=50000)
                stok_baru = st.number_input("Jumlah Stok Awal", min_value=1, step=1, value=10)
            
            submit = st.form_submit_button("💾 Simpan Produk Baru", use_container_width=True)
            if submit:
                if nama_baru.strip():
                    new_id = f"P{len(st.session_state.produk_toko) + 1:03d}"
                    st.session_state.produk_toko.append({
                        "id": new_id, "nama": nama_baru, "kategori": kat_baru,
                        "harga_jual": int(harga_baru), "stok": int(stok_baru)
                    })
                    st.success(f"✅ Produk '{nama_baru}' berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("⚠️ Nama produk wajib diisi.")

# ================= MENU 3: LAPORAN =================
elif menu == "📊 Laporan Penjualan":
    st.subheader("📊 Laporan & Analisis Penjualan")
    
    if not st.session_state.riwayat:
        st.info("Belum ada riwayat transaksi penjualan yang tercatat.")
    else:
        total_omset = sum(r["total"] for r in st.session_state.riwayat)
        total_transaksi = len(st.session_state.riwayat)
        total_item_terjual = sum(sum(i["qty"] for i in r["items"]) for r in st.session_state.riwayat)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Omset Penjualan", fmt_rp(total_omset), delta=f"{total_transaksi} Transaksi")
        k2.metric("Total Item Terjual", f"{total_item_terjual} Pcs")
        k3.metric("Rata-Rata Nilai Transaksi", fmt_rp(total_omset / total_transaksi if total_transaksi > 0 else 0))
        
        st.markdown("---")
        st.subheader("📜 Riwayat Transaksi Detail")
        
        data_riwayat = []
        for r in st.session_state.riwayat:
            data_riwayat.append({
                "ID Transaksi": r["id_transaksi"],
                "Waktu": r["waktu"],
                "Metode": r["metode"],
                "Total Item (Pcs)": sum(i["qty"] for i in r["items"]),
                "Total Pembayaran": fmt_rp(r["total"])
            })
        
        st.dataframe(pd.DataFrame(data_riwayat), use_container_width=True, hide_index=True)