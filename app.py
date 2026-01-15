import streamlit as st
import pandas as pd

st.set_page_config(page_title="MRP Karar Mekanizması", layout="wide")

st.title("🚀 Akıllı Malzeme İhtiyaç Planlama (MRP)")
st.subheader("Dosyaları yükle, satın alma kararını sistem versin.")

# 1. DOSYA YÜKLEME ALANI
with st.sidebar:
    st.header("Dosya Girişi")
    cois_file = st.file_uploader("COIS Excelini Yükle", type=['xlsx'])
    zpp028_file = st.file_uploader("ZPP028 (Ürün Ağacı) Yükle", type=['xlsx'])
    mb52_file = st.file_uploader("MB52 (Stok) Yükle", type=['xlsx'])
    me2m_file = st.file_uploader("ME2M (Açık Sipariş) Yükle", type=['xlsx'])

if cois_file and zpp028_file and mb52_file and me2m_file:
    # Verileri Oku
    df_cois = pd.read_excel(cois_file)
    df_zpp = pd.read_excel(zpp028_file)
    df_mb52 = pd.read_excel(mb52_file)
    df_me2m = pd.read_excel(me2m_file)

    # COIS: Kalan Miktar Hesabı
    df_cois['KALAN'] = df_cois['Sipariş miktarı (GMEIN)'] - df_cois['Teslim edilen miktar (GMEIN)']

    # ZPP028: İhtiyaç Patlatma (Sadece 1000 kodlu malzemeler)
    # COIS ile ZPP'yi 'Müşteri Siparişi' üzerinden birleştiriyoruz
    merged_needs = pd.merge(df_zpp[df_zpp['MALZEME TÜRÜ'] == 1000], 
                            df_cois[['Müşteri siparişi', 'Müşteri sprş.kalemi', 'KALAN', 'Pln.bşl.termini']], 
                            left_on=['MUSTERI_SIPARISI', 'KALEM'], 
                            right_on=['Müşteri siparişi', 'Müşteri sprş.kalemi'])

    merged_needs['TOPLAM_IHTIYAC'] = merged_needs['BİLEŞEN MİKTARI'] * merged_needs['KALAN']

    # MB52 & ME2M: Stok ve Yoldaki Siparişleri Grupla
    stok_durum = df_mb52.groupby('Malzeme')['Tahditsiz klnb.'].sum().reset_index()
    yoldaki_durum = df_me2m[df_me2m['Teslimatı yapılacak (miktar)'] > 0].groupby('Malzeme')['Teslimatı yapılacak (miktar)'].sum().reset_index()

    # ANA KARAR TABLOSU
    final_table = merged_needs.groupby('ÜA BİLEŞENİ')['TOPLAM_IHTIYAC'].sum().reset_index()
    final_table = pd.merge(final_table, stok_durum, left_on='ÜA BİLEŞENİ', right_on='Malzeme', how='left').fillna(0)
    final_table = pd.merge(final_table, yoldaki_durum, left_on='ÜA BİLEŞENİ', right_on='Malzeme', how='left').fillna(0)

    # NET İHTİYAÇ VE KARAR
    final_table['NET_IHTIYAC'] = final_table['TOPLAM_IHTIYAC'] - (final_table['Tahditsiz klnb.'] + final_table['Teslimatı yapılacak (miktar)'])
    final_table['AKSİYON'] = final_table['NET_IHTIYAC'].apply(lambda x: "🚨 SATIN ALMA TALEBİ AÇ" if x > 0 else "✅ STOK YETERLİ")

    st.write("### 📋 Satın Alma Karar Paneli")
    st.dataframe(final_table)

else:
    st.info("Lütfen sol taraftan tüm Excel dosyalarını yükle kanka.")
