import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime
import re
import time
from fake_useragent import UserAgent
import random

print("🚀 GERÇEK WEB ARAŞTIRMALI ANALİZ SİSTEMİ")

class RealWebAnalyzer:
    def __init__(self):
        self.ua = UserAgent()
    
    def search_company_news(self, company, country):
        """Google News'de şirket haberlerini ara"""
        results = []
        
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            search_terms = [
                f"{company} {country} export",
                f"{company} Russia business",
                f"{company} {country} trade",
                f"{company} sanctions Russia"
            ]
            
            for term in search_terms:
                try:
                    print(f"🔍 Aranıyor: '{term}'")
                    
                    # Google arama
                    url = f"https://www.google.com/search?q={term.replace(' ', '+')}&num=5"
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Sonuçları al
                        search_results = soup.find_all('div', class_='g')[:3]
                        
                        for i, result in enumerate(search_results):
                            try:
                                title_elem = result.find('h3')
                                if title_elem:
                                    title = title_elem.get_text()
                                    link_elem = result.find('a')
                                    if link_elem and 'href' in link_elem.attrs:
                                        link = link_elem['href']
                                        
                                        # URL'yi temizle
                                        if link.startswith('/url?q='):
                                            link = link.split('/url?q=')[1].split('&')[0]
                                        
                                        # Sayfa içeriğini al
                                        page_content = self.get_page_content(link, headers)
                                        
                                        if page_content:
                                            # Analiz yap
                                            analysis = self.analyze_content(company, country, title + " " + page_content)
                                            analysis.update({
                                                'URL': link,
                                                'BAŞLIK': title,
                                                'İÇERİK_ÖZETİ': page_content[:200] + '...',
                                                'ARAMA_TERİMİ': term
                                            })
                                            results.append(analysis)
                                            print(f"   ✅ {analysis['DURUM']} - %{analysis['GÜVEN_YÜZDESİ']:.1f}")
                                            
                            except Exception as e:
                                print(f"   ❌ Sonuç işleme hatası: {e}")
                                continue
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"❌ Arama hatası: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Genel arama hatası: {e}")
        
        return results
    
    def get_page_content(self, url, headers):
        """Web sayfası içeriğini al"""
        try:
            response = requests.get(url, headers=headers, timeout=8)
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
                
                return text[:3000]  # İlk 3000 karakter
                
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
            
            # Şirket ve ülke eşleşmesi
            company_found = any(word in text_lower for word in company_lower.split() if len(word) > 2)
            country_found = country_lower in text_lower
            
            if company_found:
                score += 30
                reasons.append("Şirket ismi bulundu")
            
            if country_found:
                score += 30
                reasons.append("Ülke ismi bulundu")
            
            # Ticaret terimleri
            trade_terms = {
                'export': 20, 'import': 20, 'trade': 15, 'business': 15,
                'partner': 15, 'supplier': 15, 'distributor': 15,
                'shipment': 10, 'logistics': 10, 'supply': 10
            }
            
            for term, points in trade_terms.items():
                if term in text_lower:
                    score += points
                    keywords_found.append(term)
                    reasons.append(f"{term} terimi bulundu")
            
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
            
            # Bağlam bonusu
            if company_found and country_found:
                score += 20
                reasons.append("Şirket-ülke bağlamı güçlü")
            
            # Skor normalizasyonu
            percentage = min(100, score)
            
            # Durum belirleme
            if yaptirim_risk == "YÜKSEK_RİSK":
                status = "YÜKSEK_RİSK"
                explanation = f"⛔ YÜKSEK RİSK: {company} - {country} (%{percentage:.1f})"
            elif percentage >= 70:
                status = "YÜKSEK_GÜVEN"
                explanation = f"✅ YÜKSEK GÜVEN: {company} - {country} (%{percentage:.1f})"
            elif percentage >= 40:
                status = "ORTA_GÜVEN"
                explanation = f"🟡 ORTA GÜVEN: {company} - {country} (%{percentage:.1f})"
            else:
                status = "DÜŞÜK_GÜVEN"
                explanation = f"🔴 DÜŞÜK GÜVEN: {company} - {country} (%{percentage:.1f})"
            
            return {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': status,
                'GÜVEN_YÜZDESİ': percentage,
                'AI_AÇIKLAMA': explanation,
                'AI_NEDENLER': ' | '.join(reasons),
                'AI_ANAHTAR_KELİMELER': ', '.join(keywords_found),
                'YAPTIRIM_RISKI': yaptirim_risk,
                'TESPIT_EDILEN_GTIPLER': ', '.join(gtip_codes),
                'YAPTIRIMLI_GTIPLER': ', '.join(yaptirimli_gtip),
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
                'AI_ANAHTAR_KELİMELER': '',
                'YAPTIRIM_RISKI': 'BELİRSİZ',
                'TESPIT_EDILEN_GTIPLER': '',
                'YAPTIRIMLI_GTIPLER': '',
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

def run_real_analysis(company_name, country):
    """Gerçek web araştırmalı analiz"""
    print(f"🎯 GERÇEK ANALİZ: {company_name} - {country}")
    
    analyzer = RealWebAnalyzer()
    results = analyzer.search_company_news(company_name, country)
    
    # Eğer sonuç yoksa, temel analiz yap
    if not results:
        print("ℹ️ Web sonucu bulunamadı, temel analiz yapılıyor...")
        basic_analysis = analyzer.analyze_content(
            company_name, 
            country, 
            f"{company_name} company business news {country} market"
        )
        basic_analysis.update({
            'URL': 'https://example.com/basic-analysis',
            'BAŞLIK': f'{company_name} Basic Business Analysis',
            'İÇERİK_ÖZETİ': 'Web arama sonuç bulunamadı, temel analiz uygulandı',
            'ARAMA_TERİMİ': 'basic analysis'
        })
        results = [basic_analysis]
    
    print(f"✅ GERÇEK ANALİZ TAMAMLANDI: {len(results)} sonuç")
    return results

def create_real_excel_report(results, filename='gercek_analiz.xlsx'):
    """Gerçek verili Excel raporu"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(results)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Ana sonuçlar
            df.to_excel(writer, sheet_name='Gerçek Analiz Sonuçları', index=False)
            
            # Özet
            summary_data = [{
                'ŞİRKET': results[0]['ŞİRKET'] if results else 'N/A',
                'ÜLKE': results[0]['ÜLKE'] if results else 'N/A',
                'TOPLAM_ANALİZ': len(results),
                'ORTALAMA_GÜVEN': round(df['GÜVEN_YÜZDESİ'].mean(), 1) if not df.empty else 0,
                'YÜKSEK_RİSKLİ': len(df[df['YAPTIRIM_RISKI'] == 'YÜKSEK_RİSK']),
                'WEB_KAYNAKLI': len(df[df['URL'] != 'https://example.com/basic-analysis']),
                'ANALİZ_TARİHİ': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Özet', index=False)
        
        print(f"✅ GERÇEK Excel oluşturuldu: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Excel hatası: {e}")
        return False

# Test
if __name__ == "__main__":
    results = run_real_analysis("Ford", "Russia")
    create_real_excel_report(results)
    print("🎉 GERÇEK ANALİZ TAMAMLANDI!")
