import streamlit as st
import pandas as pd

st.set_page_config(page_title="MRP Karar Mekanizması", layout="wide")

st.title("🚀 Akıllı Malzeme İhtiyaç Planlama")

# 1. DOSYA YÜKLEME
with st.sidebar:
    st.header("Dosyaları Yükle")
    cois_f = st.file_uploader("COIS Excel", type=['xlsx'])
    zpp_f = st.file_uploader("ZPP028 (Ürün Ağacı)", type=['xlsx'])
    mb52_f = st.file_uploader("MB52 (Stok)", type=['xlsx'])
    me2m_f = st.file_uploader("ME2M (Açık Sipariş)", type=['xlsx'])

if cois_f and zpp_f and mb52_f and me2m_f:
    # Verileri oku ve başındaki/sonundaki boşlukları temizle
    df_cois = pd.read_excel(cois_f)
    df_zpp = pd.read_excel(zpp_f)
    df_mb52 = pd.read_excel(mb52_f)
    df_me2m = pd.read_excel(me2m_f)

    # COIS Kalan miktar hesabı (Senin sütun isimlerine göre)
    # Görseldeki isim: 'Sipariş miktarı (GMEIN)' ve 'Teslim edilen miktar (GMEIN)'
    df_cois['KALAN'] = df_cois['Sipariş miktarı (GMEIN)'].fillna(0) - df_cois['Teslim edilen miktar (GMEIN)'].fillna(0)

    # ZPP028 Filtreleme (Sadece 1000 Kodlu Malzemeler)
    df_zpp_1000 = df_zpp[df_zpp['MALZEME TÜRÜ'] == 1000].copy()

    # İhtiyaç Patlatma (COIS ile ZPP'yi bağla)
    # Anahtar: MUSTERI_SIPARISI ve KALEM
    merged = pd.merge(
        df_zpp_1000, 
        df_cois[['Müşteri siparişi', 'Müşteri sprş.kalemi', 'KALAN']], 
        left_on=['MUSTERI_SIPARISI', 'KALEM'], 
        right_on=['Müşteri siparişi', 'Müşteri sprş.kalemi'],
        how='inner'
    )

    # Toplam İhtiyaç = Birim miktar * Kalan Sipariş
    merged['TOPLAM_IHTIYAC'] = merged['BİLEŞEN MİKTARI'] * merged['KALAN']

    # MB52 (Stok) - Malzeme bazlı topla
    stok_toplam = df_mb52.groupby('Malzeme')['Tahditsiz klnb.'].sum().reset_index()

    # ME2M (Yoldaki) - Malzeme bazlı topla
    yol_toplam = df_me2m[df_me2m['Teslimatı yapılacak (miktar)'] > 0].groupby('Malzeme')['Teslimatı yapılacak (miktar)'].sum().reset_index()

    # SONUÇ TABLOSU OLUŞTURMA
    ozet = merged.groupby('ÜA BİLEŞENİ')['TOPLAM_IHTIYAC'].sum().reset_index()
    ozet = pd.merge(ozet, stok_toplam, left_on='ÜA BİLEŞENİ', right_on='Malzeme', how='left').fillna(0)
    ozet = pd.merge(ozet, yol_toplam, left_on='ÜA BİLEŞENİ', right_on='Malzeme', how='left').fillna(0)

    # KARAR MEKANİZMASI
    ozet['NET_DURUM'] = (ozet['Tahditsiz klnb.'] + ozet['Teslimatı yapılacak (miktar)']) - ozet['TOPLAM_IHTIYAC']
    
    def karar_ver(x):
        if x < 0: return "🚨 SATIN ALMA TALEBİ AÇ"
        return "✅ STOK YETERLİ"

    ozet['KARAR'] = ozet['NET_DURUM'].apply(karar_ver)

    # Görselleştirme
    st.write("### 📊 Malzeme İhtiyaç Analizi")
    st.dataframe(ozet[['ÜA BİLEŞENİ', 'TOPLAM_IHTIYAC', 'Tahditsiz klnb.', 'Teslimatı yapılacak (miktar)', 'NET_DURUM', 'KARAR']])

else:
    st.warning("Kanka tüm dosyaları yükle de analiz başlasın.")
