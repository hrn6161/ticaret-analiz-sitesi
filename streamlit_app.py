import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime
import os
from analiz_kodu import run_analysis_for_company

st.set_page_config(
    page_title="AI Ticaret Analiz Sistemi",
    page_icon="🤖",
    layout="wide"
)

# Başlık ve açıklama
st.title("🤖 AI Ticaret Analiz Sistemi")
st.markdown("Şirketlerin Rusya ile ticaret ve yaptırım durumunu analiz edin")

# Form
with st.form("analysis_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input("Şirket Adı", placeholder="Örnek: genel oto sanayi ve ticaret as")
    
    with col2:
        country = st.selectbox("Hedef Ülke", ["", "Russia", "China", "Iran", "Turkey"], format_func=lambda x: "Ülke seçin" if x == "" else x)
    
    analyze_clicked = st.form_submit_button("🚀 Analiz Başlat")

# Analiz işlemi
if analyze_clicked:
    if not company_name or not country:
        st.error("Lütfen şirket adı ve ülke giriniz")
    else:
        with st.spinner(f"{company_name} şirketi için AI analiz yapılıyor... Bu işlem birkaç dakika sürebilir."):
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Analiz simülasyonu
            for i in range(5):
                progress_bar.progress((i + 1) * 20)
                status_text.text(f"Analiz aşaması {i + 1}/5...")
                time.sleep(1)
            
            # Gerçek analiz
            results = run_analysis_for_company(company_name, country)
            
            if results:
                df = pd.DataFrame(results)
                
                # Sonuçları göster
                st.success("✅ Analiz tamamlandı!")
                
                # Excel indirme
                excel_file = f"ticaret_analizi_{int(time.time())}.xlsx"
                df.to_excel(excel_file, index=False)
                
                with open(excel_file, "rb") as file:
                    st.download_button(
                        label="📊 Excel Dosyasını İndir",
                        data=file,
                        file_name=excel_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Sonuçları tablo olarak göster
                st.subheader("Analiz Sonuçları")
                st.dataframe(df)
                
                # Temizlik
                os.remove(excel_file)
            else:
                st.error("Analiz sonucu bulunamadı")

# Bilgi kutusu
st.sidebar.markdown("""
### ℹ️ Bilgi
- Analiz işlemi 5-10 dakika sürebilir
- Gerçek zamanlı web taraması yapılır
- AB yaptırım listesi kontrol edilir
- Excel raporu otomatik oluşturulur
""")
