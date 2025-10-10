import requests
from bs4 import BeautifulSoup
import time
import random
import re
from openpyxl import Workbook
from openpyxl.styles import Font
import sys
import logging
import os
from datetime import datetime

print("🚀 AKILLI CRAWLER ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
    
    def smart_crawl(self, url, target_country):
        """Akıllı crawl - farklı teknikler dener"""
        print(f"   🌐 Sayfa analiz ediliyor: {url}")
        
        # Önce basit requests ile dene
        result = self._crawl_with_requests(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # 403 alırsa, farklı headers ile tekrar dene
        print(f"   ⚠️  403 hatası, farklı approach deneniyor: {url}")
        result = self._crawl_with_advanced_headers(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # Hala başarısızsa, sadece DuckDuckGo snippet'ini kullan
        print(f"   ⚠️  Sayfaya erişilemedi, snippet analizi yapılacak")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': 'Sayfaya erişilemedi - Snippet analizi yapıldı', 'status_code': 'SNIPPET_ONLY'}
    
    def _crawl_with_requests(self, url, target_country):
        """Basit requests ile crawl"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                return self._parse_content(response.text, url, target_country, response.status_code)
            else:
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ Crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _crawl_with_advanced_headers(self, url, target_country):
        """Gelişmiş headers ile crawl"""
        try:
            print(f"   🔧 Gelişmiş headers ile deneniyor...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            # Session kullan
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                return self._parse_content(response.text, url, target_country, response.status_code)
            else:
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ Gelişmiş crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_content(self, html, url, target_country, status_code):
        """Sayfa içeriğini parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Script ve style tag'lerini temizle
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Meta description'ı da al
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_content = meta_desc.get('content', '') if meta_desc else ''
        
        # Tüm metni al
        text_content = soup.get_text()
        combined_content = f"{meta_content} {text_content}"
        
        # Temizleme
        lines = (line.strip() for line in combined_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_content = ' '.join(chunk for chunk in chunks if chunk)
        
        text_lower = cleaned_content.lower()
        
        # Ülke ismini ara
        country_found = target_country.lower() in text_lower
        
        # GTIP/HS kodlarını ara
        gtip_codes = self.extract_gtip_codes(cleaned_content)
        
        content_preview = cleaned_content[:400] + "..." if len(cleaned_content) > 400 else cleaned_content
        
        print(f"   🔍 Sayfa analizi: Ülke bulundu={country_found}, GTIP kodları={gtip_codes}")
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': content_preview,
            'status_code': status_code
        }
    
    def extract_gtip_codes(self, text):
        """Metinden GTIP/HS kodlarını çıkar"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bHS\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
            r'\bHarmonized System\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bCustoms\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bTariff\s?Code\s?:?\s?(\d{4,8})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    main_code = code[:4]
                    if main_code.isdigit():
                        all_codes.add(main_code)
        
        # 4 haneli sayıları kontrol et (GTIP aralığında mı)
        number_pattern = r'\b\d{4}\b'
        numbers = re.findall(number_pattern, text)
        
        for num in numbers:
            if num.isdigit():
                num_int = int(num)
                # Geniş GTIP aralıkları
                if ((8400 <= num_int <= 8600) or (8700 <= num_int <= 8900) or 
                    (9000 <= num_int <= 9300) or (2800 <= num_int <= 2900) or
                    (8470 <= num_int <= 8480) or (8500 <= num_int <= 8520) or
                    (8540 <= num_int <= 8550) or (9301 <= num_int <= 9307)):
                    all_codes.add(num)
        
        return list(all_codes)

class DuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
    
    def search_duckduckgo(self, query, max_results=3):
        """DuckDuckGo'da arama yap"""
        try:
            print(f"🔍 DuckDuckGo'da aranıyor: {query}")
            
            query = query.replace('"', '')
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            url = "https://html.duckduckgo.com/html/"
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                return self.parse_duckduckgo_results(response.text, max_results)
            else:
                print(f"❌ DuckDuckGo arama hatası: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ DuckDuckGo arama hatası: {e}")
            return []
    
    def parse_duckduckgo_results(self, html, max_results):
        """DuckDuckGo sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        result_divs = soup.find_all('div', class_='result')
        
        for div in result_divs[:max_results]:
            try:
                title_elem = div.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                url = title_elem.get('href')
                if url and '//duckduckgo.com/l/' in url:
                    try:
                        redirect_response = requests.get(url, timeout=10, allow_redirects=True)
                        url = redirect_response.url
                    except:
                        pass
                
                snippet_elem = div.find('a', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if url and url.startswith('//'):
                    url = 'https:' + url
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'full_text': f"{title} {snippet}"  # Snippet analizi için
                })
                
                print(f"   📄 Bulunan sonuç: {title[:60]}...")
                
            except Exception as e:
                print(f"   ❌ Sonuç parse hatası: {e}")
                continue
        
        print(f"✅ DuckDuckGo'dan {len(results)} sonuç bulundu")
        return results

class EURLexChecker:
    def __init__(self, config):
        self.config = config
    
    def check_gtip_in_eur_lex(self, gtip_codes):
        """GTIP kodlarını EUR-Lex'te kontrol et"""
        sanctioned_codes = []
        
        for gtip_code in gtip_codes:
            try:
                print(f"   🔍 EUR-Lex'te kontrol ediliyor: GTIP {gtip_code}")
                
                time.sleep(random.uniform(1, 2))
                
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'qid': int(time.time()),
                    'text': f'"{gtip_code}" prohibited banned sanction restricted embargo',
                    'type': 'advanced',
                    'lang': 'en'
                }
                
                headers = {
                    'User-Agent': random.choice(self.config.USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.get_text().lower()
                    
                    sanction_terms = [
                        'prohibited', 'banned', 'sanction', 'restricted', 
                        'embargo', 'forbidden', 'prohibition', 'ban',
                        'not allowed', 'not permitted', 'restriction'
                    ]
                    found_sanction = any(term in content for term in sanction_terms)
                    
                    if found_sanction:
                        sanctioned_codes.append(gtip_code)
                        print(f"   ⛔ Yaptırımlı kod bulundu: {gtip_code}")
                    else:
                        print(f"   ✅ Kod temiz: {gtip_code}")
                else:
                    print(f"   ❌ EUR-Lex erişim hatası: {response.status_code}")
                
            except Exception as e:
                print(f"   ❌ EUR-Lex kontrol hatası GTIP {gtip_code}: {e}")
                continue
        
        return sanctioned_codes

class AdvancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = DuckDuckGoSearcher(config)
        self.crawler = SmartCrawler(config)
        self.eur_lex_checker = EURLexChecker(config)
    
    def analyze_company_country(self, company, country):
        """Şirket-ülke analizi yap"""
        print(f"🤖 AKILLI ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business",
            f"{company} {country} trade",
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"\n🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                search_results = self.searcher.search_duckduckgo(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    print(f"   ⚠️ Bu sorgu için sonuç bulunamadı")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    print(f"   📄 Sonuç {j} analiz ediliyor: {result['title'][:50]}...")
                    
                    # Akıllı crawl et
                    crawl_result = self.crawler.smart_crawl(result['url'], country)
                    
                    # Eğer sayfaya erişilemediyse, snippet'ten GTIP kodlarını çıkar
                    if crawl_result['status_code'] != 200 and 'full_text' in result:
                        snippet_gtips = self.crawler.extract_gtip_codes(result['full_text'])
                        if snippet_gtips:
                            crawl_result['gtip_codes'] = snippet_gtips
                            crawl_result['content_preview'] = 'Snippet analizi: ' + result['snippet'][:200]
                            print(f"   🔍 Snippet'ten GTIP kodları çıkarıldı: {snippet_gtips}")
                    
                    # EUR-Lex kontrolü
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        print(f"   🔍 EUR-Lex kontrolü yapılıyor...")
                        sanctioned_gtips = self.eur_lex_checker.check_gtip_in_eur_lex(crawl_result['gtip_codes'])
                    
                    # Analiz sonucu oluştur
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips
                    )
                    
                    all_results.append(analysis)
                
                # Sorgular arasında bekleme
                if i < len(search_queries):
                    delay = random.uniform(2, 4)
                    print(f"   ⏳ {delay:.1f} saniye bekleniyor (sorgular arası)...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"   ❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def create_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips):
        """Analiz sonucu oluştur"""
        
        if sanctioned_gtips:
            status = "YAPTIRIMLI_YÜKSEK_RISK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
            ai_tavsiye = f"⛔ ACİL DURUM! Bu ürünlerin {country.upper()} ihracı YASAKTIR: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif crawl_result['country_found'] and crawl_result['gtip_codes']:
            status = "RISK_VAR"
            explanation = f"🟡 RİSK VAR: {company} şirketi {country} ile ticaret bağlantısı bulundu"
            ai_tavsiye = f"Ticaret bağlantısı doğrulandı. GTIP kodları: {', '.join(crawl_result['gtip_codes'])}"
            risk_level = "ORTA"
        elif crawl_result['country_found']:
            status = "İLİŞKİ_VAR"
            explanation = f"🟢 İLİŞKİ VAR: {company} şirketi {country} ile bağlantılı"
            ai_tavsiye = "Ticaret bağlantısı bulundu ancak GTIP kodu tespit edilemedi"
            risk_level = "DÜŞÜK"
        else:
            status = "TEMIZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile ticaret bağlantısı bulunamadı"
            ai_tavsiye = "Ticaret bağlantısı bulunamadı"
            risk_level = "YOK"
        
        return {
            'ŞİRKET': company,
            'ÜLKE': country,
            'DURUM': status,
            'AI_AÇIKLAMA': explanation,
            'AI_TAVSIYE': ai_tavsiye,
            'YAPTIRIM_RISKI': risk_level,
            'TESPIT_EDILEN_GTIPLER': ', '.join(crawl_result['gtip_codes']),
            'YAPTIRIMLI_GTIPLER': ', '.join(sanctioned_gtips),
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
            'BAŞLIK': search_result['title'],
            'URL': search_result['url'],
            'ÖZET': search_result['snippet'],
            'CONTENT_PREVIEW': crawl_result['content_preview'],
            'STATUS_CODE': crawl_result.get('status_code', 'N/A'),
            'CRAWLER_TIPI': 'AKILLI_CRAWLER'
        }

def create_excel_report(results, company, country):
    """Excel raporu oluştur"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_akilli_analiz.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Akıllı Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA',
            'AI_TAVSIYE', 'BAŞLIK', 'URL', 'CRAWLER_TIPI'
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header).font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            ws.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws.cell(row=row, column=4, value=str(result.get('YAPTIRIM_RISKI', '')))
            ws.cell(row=row, column=5, value=str(result.get('ULKE_BAGLANTISI', '')))
            ws.cell(row=row, column=6, value=str(result.get('TESPIT_EDILEN_GTIPLER', '')))
            ws.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTIPLER', '')))
            ws.cell(row=row, column=8, value=str(result.get('AI_AÇIKLAMA', '')))
            ws.cell(row=row, column=9, value=str(result.get('AI_TAVSIYE', '')))
            ws.cell(row=row, column=10, value=str(result.get('BAŞLIK', '')))
            ws.cell(row=row, column=11, value=str(result.get('URL', '')))
            ws.cell(row=row, column=12, value=str(result.get('CRAWLER_TIPI', '')))
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(filename)
        print(f"✅ Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel rapor oluşturma hatası: {e}")
        return None

def display_results(results, company, country):
    """Sonuçları ekranda göster"""
    print(f"\n{'='*80}")
    print(f"📊 AKILLI ANALİZ SONUÇLARI: {company} ↔ {country}")
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
    print(f"   • Crawler Tipi: AKILLI CRAWLER (403 Atlama)")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK YAPTIRIM UYARISI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YÜKSEK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:60]}...")
                print(f"      Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
    
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
        print(f"   📊 Status Code: {result.get('STATUS_CODE', 'N/A')}")
        print(f"   🤖 Crawler: {result.get('CRAWLER_TIPI', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 AKILLI CRAWLER ANALİZ SİSTEMİ")
    print("🌐 ÖZELLİK: 403 Hata Atlama + Snippet Analizi")
    print("💡 AVANTAJ: Selenium gerekmez, hızlı çalışır, Docker sorunu yok!")
    print("🎯 STRATEJİ: Önce basit, sonra gelişmiş headers, en son snippet analizi\n")
    
    # Yapılandırma
    config = Config()
    analyzer = AdvancedTradeAnalyzer(config)
    
    # Manuel giriş
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 AKILLI ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
    print("⏳ DuckDuckGo'da arama yapılıyor...")
    print("   Akıllı crawler 403 hatalarını aşmaya çalışacak!")
    print("   Sayfalara erişilemezse snippet analizi yapılacak...\n")
    
    start_time = time.time()
    results = analyzer.analyze_company_country(company, country)
    execution_time = time.time() - start_time
    
    if results:
        # Sonuçları göster
        display_results(results, company, country)
        
        # Excel raporu oluştur
        filename = create_excel_report(results, company, country)
        
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
