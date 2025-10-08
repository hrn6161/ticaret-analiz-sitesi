import requests
import pandas as pd
import re
import time
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from bs4 import BeautifulSoup
import random

print("🚀 ARAMA MOTORU ANALİZ SİSTEMİ BAŞLATILIYOR...")

class SearchEngineAnalyzer:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def search_google(self, company, country):
        """Google'da arama yap"""
        all_results = []
        
        search_terms = [
            f"{company} {country} export",
            f"{company} {country} business Russia", 
            f"{company} Russia trade",
            f"{company} {country} sanctions"
        ]
        
        for term in search_terms:
            try:
                print(f"🔍 Google'da aranıyor: '{term}'")
                
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                url = f"https://www.google.com/search?q={term.replace(' ', '+')}&num=10"
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Google arama sonuçlarını al
                    results = soup.find_all('div', class_='g')[:5]
                    
                    for i, result in enumerate(results):
                        try:
                            title_elem = result.find('h3')
                            link_elem = result.find('a')
                            
                            if title_elem and link_elem:
                                title = title_elem.get_text()
                                url = link_elem['href']
                                
                                # URL'yi temizle
                                if url.startswith('/url?q='):
                                    url = url.split('/url?q=')[1].split('&')[0]
                                
                                print(f"   📄 {i+1}. {title[:50]}...")
                                
                                # Sayfa içeriğini al
                                page_content = self.get_page_content(url, headers)
                                
                                if page_content:
                                    # Analiz yap
                                    analysis = self.analyze_content(company, country, title + " " + page_content)
                                    analysis.update({
                                        'URL': url,
                                        'BAŞLIK': title,
                                        'İÇERİK_ÖZETİ': page_content[:200] + '...',
                                        'ARAMA_TERİMİ': term,
                                        'ARAMA_MOTORU': 'Google'
                                    })
                                    all_results.append(analysis)
                                    print(f"     ✅ {analysis['DURUM']} - %{analysis['GÜVEN_YÜZDESİ']:.1f}")
                                    
                        except Exception as e:
                            print(f"     ❌ Sonuç işleme hatası: {e}")
                            continue
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Arama hatası: {e}")
                continue
        
        return all_results
    
    def search_bing(self, company, country):
        """Bing'de arama yap"""
        all_results = []
        
        search_terms = [
            f"{company} {country} export",
            f"{company} Russia business"
        ]
        
        for term in search_terms:
            try:
                print(f"🔍 Bing'de aranıyor: '{term}'")
                
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
                
                url = f"https://www.bing.com/search?q={term.replace(' ', '+')}&count=10"
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Bing arama sonuçlarını al
                    results = soup.find_all('li', class_='b_algo')[:5]
                    
                    for i, result in enumerate(results):
                        try:
                            title_elem = result.find('h2')
                            link_elem = result.find('a')
                            
                            if title_elem and link_elem:
                                title = title_elem.get_text()
                                url = link_elem['href']
                                
                                print(f"   📄 {i+1}. {title[:50]}...")
                                
                                # Sayfa içeriğini al
                                page_content = self.get_page_content(url, headers)
                                
                                if page_content:
                                    # Analiz yap
                                    analysis = self.analyze_content(company, country, title + " " + page_content)
                                    analysis.update({
                                        'URL': url,
                                        'BAŞLIK': title,
                                        'İÇERİK_ÖZETİ': page_content[:200] + '...',
                                        'ARAMA_TERİMİ': term,
                                        'ARAMA_MOTORU': 'Bing'
                                    })
                                    all_results.append(analysis)
                                    print(f"     ✅ {analysis['DURUM']} - %{analysis['GÜVEN_YÜZDESİ']:.1f}")
                                    
                        except Exception as e:
                            print(f"     ❌ Sonuç işleme hatası: {e}")
                            continue
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Arama hatası: {e}")
                continue
        
        return all_results
    
    def get_page_content(self, url, headers):
        """Web sayfası içeriğini al"""
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Script ve style tag'lerini temizle
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                # Fazla boşlukları temizle
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text[:2500]  # İlk 2500 karakter
                
        except Exception as e:
            print(f"   ❌ Sayfa okuma hatası: {e}")
        
        return None
    
    def analyze_content(self, company, country, text):
        """İçeriği analiz et"""
        try:
            text_lower = text.lower()
            company_lower = company.lower()
            country_lower = country.lower()
            
            score = 0
            reasons = []
            keywords_found = []
            confidence_factors = []
            detected_products = []
            
            # Şirket ve ülke kontrolü
            company_words = [word for word in company_lower.split() if len(word) > 3]
            company_found = any(word in text_lower for word in company_words)
            country_found = country_lower in text_lower
            
            if company_found:
                score += 30
                reasons.append("Şirket ismi bulundu")
                confidence_factors.append("Şirket tanımlı")
            
            if country_found:
                score += 30
                reasons.append("Ülke ismi bulundu")
                confidence_factors.append("Hedef ülke tanımlı")
            
            # Ticaret göstergeleri
            trade_indicators = {
                'export': 20, 'import': 20, 'trade': 15, 'business': 15,
                'partner': 15, 'supplier': 15, 'distributor': 15,
                'shipment': 10, 'logistics': 10, 'supply': 10
            }
            
            for term, points in trade_indicators.items():
                if term in text_lower:
                    score += points
                    keywords_found.append(term)
                    reasons.append(f"{term} terimi bulundu")
            
            # Ürün tespiti
            product_keywords = {
                'automotive': '8703', 'vehicle': '8703', 'car': '8703', 'truck': '8701',
                'parts': '8708', 'component': '8708', 'engine': '8407', 'motor': '8407',
                'computer': '8471', 'electronic': '8542', 'chip': '8542', 'semiconductor': '8542'
            }
            
            for product, gtip in product_keywords.items():
                if product in text_lower:
                    detected_products.append(f"{product}({gtip})")
                    reasons.append(f"{product} ürün kategorisi tespit edildi (GTIP: {gtip})")
            
            # GTIP kodları
            gtip_codes = self.extract_gtip_codes(text)
            
            # Yaptırım riski
            yaptirim_risk = "DÜŞÜK"
            yaptirimli_gtip = []
            
            if country_lower in ['russia', 'rusya'] and gtip_codes:
                yasakli_gtip = ['8703', '8708', '8407', '8471', '8542']
                for code in gtip_codes:
                    if code in yasakli_gtip:
                        yaptirim_risk = "YÜKSEK_RİSK"
                        yaptirimli_gtip.append(code)
                        reasons.append(f"Yasaklı GTIP: {code}")
            
            # Bağlam analizi
            context_phrases = [
                f"{company_lower}.*{country_lower}",
                f"export.*{country_lower}",
                f"business.*{country_lower}",
                f"partner.*{country_lower}"
            ]
            
            context_matches = 0
            for phrase in context_phrases:
                if re.search(phrase, text_lower.replace(" ", "")):
                    context_matches += 1
                    reasons.append(f"Bağlam eşleşmesi: {phrase}")
            
            if context_matches >= 1:
                score += 15
                confidence_factors.append("Güçlü bağlam")
            
            # Çeşitlilik bonusu
            unique_trade_terms = len(set(keywords_found))
            if unique_trade_terms >= 3:
                score += 10
                reasons.append(f"{unique_trade_terms} farklı ticaret terimi")
                confidence_factors.append("Zengin terminoloji")
            
            # İçerik uzunluğu
            word_count = len(text_lower.split())
            if word_count > 300:
                score += 5
                confidence_factors.append("Detaylı içerik")
            
            # Skor normalizasyonu
            percentage = min(100, (score / 150) * 100)
            
            # Durum belirleme
            if yaptirim_risk == "YÜKSEK_RİSK":
                status = "YÜKSEK_RİSK"
                explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yasaklı ürün ticareti (%{percentage:.1f})"
            elif percentage >= 70:
                status = "YÜKSEK_GÜVEN"
                explanation = f"✅ YÜKSEK GÜVEN: {company} şirketi {country} ile güçlü ticaret ilişkisi (%{percentage:.1f})"
            elif percentage >= 50:
                status = "ORTA_GÜVEN"
                explanation = f"🟡 ORTA GÜVEN: {company} şirketinin {country} ile ticaret olasılığı (%{percentage:.1f})"
            elif percentage >= 30:
                status = "DÜŞÜK_GÜVEN"
                explanation = f"🟢 DÜŞÜK GÜVEN: {company} şirketinin {country} ile sınırlı ticaret belirtileri (%{percentage:.1f})"
            else:
                status = "BELİRSİZ"
                explanation = f"⚪ BELİRSİZ: {company} şirketinin {country} ile ticaret ilişkisi kanıtı yok (%{percentage:.1f})"
            
            return {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': status,
                'GÜVEN_YÜZDESİ': percentage,
                'AI_AÇIKLAMA': explanation,
                'AI_NEDENLER': ' | '.join(reasons),
                'AI_GÜVEN_FAKTÖRLERİ': ' | '.join(confidence_factors),
                'AI_ANAHTAR_KELİMELER': ', '.join(keywords_found),
                'AI_ANALİZ_TİPİ': 'Arama Motoru Analizi',
                'METİN_UZUNLUĞU': word_count,
                'YAPTIRIM_RISKI': yaptirim_risk,
                'TESPIT_EDILEN_GTIPLER': ', '.join(gtip_codes),
                'YAPTIRIMLI_GTIPLER': ', '.join(yaptirimli_gtip),
                'TESPIT_EDILEN_URUNLER': ', '.join(detected_products),
                'TARİH': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'HATA',
                'GÜVEN_YÜZDESİ': 0,
                'AI_AÇIKLAMA': f'Analiz hatası: {str(e)}',
                'AI_NEDENLER': '',
                'AI_GÜVEN_FAKTÖRLERİ': '',
                'AI_ANAHTAR_KELİMELER': '',
                'AI_ANALİZ_TİPİ': 'Hata',
                'METİN_UZUNLUĞU': 0,
                'YAPTIRIM_RISKI': 'BELİRSİZ',
                'TESPIT_EDILEN_GTIPLER': '',
                'YAPTIRIMLI_GTIPLER': '',
                'TESPIT_EDILEN_URUNLER': '',
                'TARİH': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def extract_gtip_codes(self, text):
        """Metinden GTIP kodlarını çıkar"""
        gtip_pattern = r'\b\d{4}(?:\.\d{2,4})?\b'
        codes = re.findall(gtip_pattern, text)
        
        main_codes = set()
        for code in codes:
            main_code = code.split('.')[0]
            if len(main_code) == 4:
                main_codes.add(main_code)
        
        return list(main_codes)[:5]

def run_search_engine_analysis(company_name, country):
    """Arama motoru analizi çalıştır"""
    print(f"🎯 ARAMA MOTORU ANALİZİ: {company_name} - {country}")
    
    analyzer = SearchEngineAnalyzer()
    
    # Hem Google hem Bing'de ara
    google_results = analyzer.search_google(company_name, country)
    bing_results = analyzer.search_bing(company_name, country)
    
    all_results = google_results + bing_results
    
    # Eğer sonuç yoksa, temel analiz yap
    if not all_results:
        print("ℹ️ Arama sonucu bulunamadı, temel analiz yapılıyor...")
        basic_analysis = analyzer.analyze_content(
            company_name, 
            country, 
            f"{company_name} company {country} market export trade business analysis"
        )
        basic_analysis.update({
            'URL': 'https://www.google.com',
            'BAŞLIK': f'{company_name} Market Analysis',
            'İÇERİK_ÖZETİ': 'Arama sonucu bulunamadı, temel analiz uygulandı',
            'ARAMA_TERİMİ': 'basic analysis',
            'ARAMA_MOTORU': 'Temel Analiz'
        })
        all_results = [basic_analysis]
    
    print(f"✅ ARAMA MOTORU ANALİZİ TAMAMLANDI: {len(all_results)} sonuç")
    return all_results

def create_excel_report(results, filename='arama_analiz.xlsx'):
    """Excel raporu oluştur"""
    try:
        df = pd.DataFrame(results)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Ana sonuçlar
            df.to_excel(writer, sheet_name='Arama Analiz Sonuçları', index=False)
            
            # Yüksek riskliler
            high_risk = df[df['YAPTIRIM_RISKI'] == 'YÜKSEK_RİSK']
            if not high_risk.empty:
                high_risk.to_excel(writer, sheet_name='Yüksek Riskli', index=False)
            
            # Özet
            if not df.empty:
                summary_data = [{
                    'ŞİRKET': results[0]['ŞİRKET'],
                    'ÜLKE': results[0]['ÜLKE'],
                    'TOPLAM_ANALİZ': len(results),
                    'ORTALAMA_GÜVEN': round(df['GÜVEN_YÜZDESİ'].mean(), 1),
                    'MAX_GÜVEN': round(df['GÜVEN_YÜZDESİ'].max(), 1),
                    'YÜKSEK_RİSK_SAYISI': len(high_risk),
                    'GOOGLE_SONUÇ': len([r for r in results if r.get('ARAMA_MOTORU') == 'Google']),
                    'BING_SONUÇ': len([r for r in results if r.get('ARAMA_MOTORU') == 'Bing']),
                    'ANALİZ_TARİHİ': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Özet', index=False)
        
        print(f"✅ Excel raporu oluşturuldu: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Excel hatası: {e}")
        return False

# Test
if __name__ == "__main__":
    results = run_search_engine_analysis("Toyota", "Russia")
    create_excel_report(results)
    print("🎉 ARAMA MOTORU ANALİZİ TAMAMLANDI!")
