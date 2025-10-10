# ... önceki kod aynı kalacak ...

        # Yapay Zeka Yorumu
        ws2.cell(row=13, column=1, value="YAPAY ZEKA ANALİZ YORUMU:").font = Font(bold=True)
        
        if high_risk_count > 0:
            yorum = f"KRİTİK RİSK! {company} şirketinin {country} ile yaptırımlı ürün ticareti tespit edildi. "
            yorum += f"Toplam {high_risk_count} farklı kaynakta yaptırımlı GTIP kodları bulundu. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Acil önlem alınması gerekmektedir."
        elif medium_risk_count > 0:
            yorum = f"ORTA RİSK! {company} şirketinin {country} ile ticaret bağlantısı bulundu. "
            yorum += f"{medium_risk_count} farklı kaynakta ticaret ilişkisi doğrulandı. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Detaylı inceleme önerilir."
        elif country_connection_count > 0:
            yorum = f"DÜŞÜK RİSK! {company} şirketinin {country} ile bağlantısı bulundu ancak yaptırım riski tespit edilmedi. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Standart ticaret prosedürleri uygulanabilir."
        else:
            yorum = f"TEMİZ! {company} şirketinin {country} ile ticaret bağlantısı bulunamadı. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Herhangi bir yaptırım riski tespit edilmedi."
        
        ws2.cell(row=14, column=1, value=yorum)
        
        # Tavsiyeler
        ws2.cell(row=16, column=1, value="YAPAY ZEKA TAVSİYELERİ:").font = Font(bold=True)
        
        if high_risk_count > 0:
            tavsiye = "1. Yaptırımlı ürün ihracından acilen kaçının\n"
            tavsiye += "2. Yasal danışmanla görüşün\n"
            tavsiye += "3. Ticaret partnerlerini yeniden değerlendirin\n"
            tavsiye += "4. Uyum birimini bilgilendirin"
        elif medium_risk_count > 0:
            tavsiye = "1. Detaylı due diligence yapın\n"
            tavsiye += "2. Ticaret dokümanlarını kontrol edin\n"
            tavsiye += "3. Güncel yaptırım listelerini takip edin\n"
            tavsiye += "4. Alternatif pazarları değerlendirin"
        else:
            tavsiye = "1. Standart ticaret prosedürlerine devam edin\n"
            tavsiye += "2. Pazar araştırmalarını sürdürün\n"
            tavsiye += "3. Düzenli olarak kontrol edin\n"
            tavsiye += "4. Yeni iş fırsatlarını değerlendirin"
        
        ws2.cell(row=17, column=1, value=tavsiye)
        
        # Kaynaklar
        ws2.cell(row=19, column=1, value="ANALİZ EDİLEN KAYNAKLAR:").font = Font(bold=True)
        
        for i, result in enumerate(results[:5], 1):
            ws2.cell(row=20 + i, column=1, value=f"{i}. {result.get('BAŞLIK', '')}")
            ws2.cell(row=20 + i, column=2, value=result.get('URL', ''))
            ws2.cell(row=20 + i, column=3, value=result.get('GÜVEN_SEVİYESİ', ''))
        
        # Stil ayarları
        for column in ws1.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws1.column_dimensions[column_letter].width = adjusted_width
        
        ws2.column_dimensions['A'].width = 25
        ws2.column_dimensions['B'].width = 50
        ws2.column_dimensions['C'].width = 15
        
        wb.save(filename)
        print(f"✅ Detaylı Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel rapor oluşturma hatası: {e}")
        return None

def display_results(results, company, country):
    """Sonuçları ekranda göster"""
    print(f"\n{'='*80}")
    print(f"📊 GELİŞMİŞ TİCARET ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    
    print(f"\n📈 ÖZET:")
    print(f"   • Toplam Sonuç: {total_results}")
    print(f"   • Ülke Bağlantısı: {country_connection_count}")
    print(f"   • YÜKSEK Yaptırım Riski: {high_risk_count}")
    print(f"   • ORTA Risk: {medium_risk_count}")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK YAPTIRIM UYARISI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YÜKSEK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:60]}...")
                print(f"      Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
                print(f"      Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', '')}")
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   📋 Özet: {result.get('ÖZET', 'N/A')[:100]}...")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Yaptırım Riski: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        if result.get('YAPTIRIMLI_GTIPLER'):
            print(f"   🚫 Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
        print(f"   📊 Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   📋 Nedenler: {result.get('NEDENLER', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ")
    print("🎯 ÖZELLİK: Gelişmiş Snippet Analizi + Güven Seviyesi")
    print("💡 AVANTAJ: TRADEMO.COM HS Code 870830 ve Country of Export tespiti")
    print("🚀 HEDEF: Kritik ticaret verilerini otomatik tespit etme\n")
    
    # Yapılandırma
    config = Config()
    analyzer = EnhancedTradeAnalyzer(config)
    
    # Manuel giriş
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 GELİŞMİŞ ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
    print("⏳ DuckDuckGo'da gelişmiş arama yapılıyor...")
    print("   Snippet derinlemesine analiz ediliyor...")
    print("   TRADEMO.COM HS Code ve Country of Export taranıyor...")
    print("   Güven seviyesi hesaplanıyor...\n")
    
    start_time = time.time()
    results = analyzer.enhanced_analyze(company, country)
    execution_time = time.time() - start_time
    
    if results:
        # Sonuçları göster
        display_results(results, company, country)
        
        # Excel raporu oluştur
        filename = create_detailed_excel_report(results, company, country)
        
        if filename:
            print(f"\n✅ Excel raporu oluşturuldu: {filename}")
            print(f"⏱️  Toplam çalışma süresi: {execution_time:.2f} saniye")
            
            # Excel açma seçeneği
            try:
                open_excel = input("\n📂 Excel dosyasını şimdi açmak ister misiniz? (e/h): ").strip().lower()
                if open_excel == 'e':
                    if os.name == 'nt':  # Windows
                        os.system(f'start excel "{filename}"')
                    elif os.name == 'posix':  # macOS/Linux
                        os.system(f'open "{filename}"' if sys.platform == 'darwin' else f'xdg-open "{filename}"')
                    print("📂 Excel dosyası açılıyor...")
            except Exception as e:
                print(f"⚠️  Dosya otomatik açılamadı: {e}")
                print(f"📁 Lütfen manuel olarak açın: {filename}")
        else:
            print("❌ Excel raporu oluşturulamadı!")
    else:
        print("❌ Analiz sonucu bulunamadı!")

if __name__ == "__main__":
    main()
