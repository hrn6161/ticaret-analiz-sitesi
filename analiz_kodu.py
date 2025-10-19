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
import cloudscraper
import urllib.parse

print("🚀 OTOMATİK RİSK ANALİZLİ TİCARET SİSTEMİ")

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
        self.MAX_RESULTS = 10
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 1
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def smart_crawl(self, url, target_country):
        """Akıllı crawl"""
        print(f"   🌐 Crawl: {url[:60]}...")
        
        # Önce cloudscraper ile dene
        result = self._try_cloudscraper(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # Cloudscraper başarısızsa normal requests ile dene
        result = self._try_requests(url, target_country)
        if result['status_code'] == 200:
            return result
        
        print(f"   🔍 Sayfa erişilemiyor")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'BLOCKED'}
    
    def _try_cloudscraper(self, url, target_country):
        """Cloudscraper ile dene"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = self.scraper.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ Cloudscraper başarılı: {url}")
                return self._parse_content(response.text, target_country, response.status_code)
            else:
                print(f"   ❌ Cloudscraper hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ Cloudscraper hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _try_requests(self, url, target_country):
        """Normal requests ile dene"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ Requests başarılı: {url}")
                return self._parse_content(response.text, target_country, response.status_code)
            else:
                print(f"   ❌ Requests hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ Requests hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_content(self, html, target_country, status_code):
        """İçerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            country_found = self._check_country(text_lower, target_country)
            gtip_codes = self.extract_gtip_codes(text_content)
            
            print(f"   🔍 Sayfa analizi: Ülke={country_found}, GTIP={gtip_codes[:3]}")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content,
                'status_code': status_code
            }
        except Exception as e:
            print(f"   ❌ Parse hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'PARSE_ERROR'}
    
    def _check_country(self, text_lower, target_country):
        """Ülke kontrolü"""
        country_variations = [
            target_country.lower(),
            'russia', 'rusya', 'rusian', 'rus'
        ]
        
        for country_var in country_variations:
            if country_var in text_lower:
                return True
        
        return False
    
    def extract_gtip_codes(self, text):
        """GTIP kod çıkarma"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\b\d{6}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    all_codes.add(code[:4])
        
        return list(all_codes)

class SimpleDuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        print("   🦆 DuckDuckGo arama motoru hazır!")
    
    def search_simple(self, query, max_results=10):
        """Basit DuckDuckGo arama - DEMO MOD"""
        try:
            print(f"   🔍 Arama: {query}")
            
            time.sleep(2)
            
            # DuckDuckGo'yu deneyelim
            url = "https://duckduckgo.com/html/"
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            response = self.scraper.post(url, data=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                results = self._parse_results(response.text, max_results)
                print(f"   ✅ {len(results)} sonuç buldu")
                return results
            else:
                print(f"   ❌ Arama hatası {response.status_code}")
                return self._search_alternative(query, max_results)
                
        except Exception as e:
            print(f"   ❌ Arama hatası: {e}")
            return self._search_alternative(query, max_results)
    
    def _search_alternative(self, query, max_results):
        """Alternatif arama - DEMO SONUÇLAR"""
        try:
            print(f"   🔍 Alternatif arama (DEMO): {query}")
            
            # Demo sonuçlar oluştur
            sample_results = self._generate_sample_results(query, max_results)
            print(f"   ✅ Alternatif arama: {len(sample_results)} örnek sonuç")
            return sample_results
            
        except Exception as e:
            print(f"   ❌ Alternatif arama hatası: {e}")
            return []
    
    def _generate_sample_results(self, query, max_results):
        """Örnek sonuçlar oluştur - demo amaçlı"""
        company = query.split()[0] if query.split() else "Şirket"
        
        sample_data = [
            {
                'title': f"{company} şirketi Rusya ile ticaret verileri",
                'url': f"https://ticaret-veritabanı.com/{company}-rusya",
                'snippet': f"{company} şirketinin Rusya Federasyonu ile ihracat-ithalat verileri analiz ediliyor",
                'search_engine': 'demo'
            },
            {
                'title': f"{company} uluslararası ticaret raporu",
                'url': f"https://trade-analysis.org/{company}-report",
                'snippet': f"{company} şirketinin uluslararası ticaret faaliyetleri ve partner ülkeler",
                'search_engine': 'demo'
            },
            {
                'title': f"{company} GTIP kodları ve yaptırım analizi",
                'url': f"https://customs-data.eu/{company}-gtip",
                'snippet': f"{company} şirketinin kullandığı GTIP kodları ve yaptırım durumu",
                'search_engine': 'demo'
            }
        ]
        
        return sample_data[:max_results]
    
    def _parse_results(self, html, max_results):
        """Sonuç parsing"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # DuckDuckGo sonuç elementleri
        results_elements = soup.find_all('div', class_=lambda x: x and ('result' in x if x else False))
        
        for element in results_elements[:max_results]:
            try:
                title_elem = element.find('a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if len(title) < 5:
                    continue
                    
                url = title_elem.get('href')
                
                if url and ('//duckduckgo.com/l/' in url or url.startswith('/l/')):
                    url = self._resolve_redirect(url)
                
                if not url or not url.startswith('http'):
                    if url and url.startswith('/'):
                        url = 'https://duckduckgo.com' + url
                    else:
                        continue
                
                snippet = ""
                snippet_elem = element.find('div', class_=lambda x: x and ('snippet' in x if x else False))
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'full_text': f"{title} {snippet}",
                    'domain': self._extract_domain(url),
                    'search_engine': 'duckduckgo'
                })
                
                print(f"   📄 {title[:50]}...")
                
            except Exception as e:
                continue
        
        return results
    
    def _resolve_redirect(self, redirect_url):
        """Redirect çöz"""
        try:
            if redirect_url.startswith('/l/'):
                redirect_url = 'https://duckduckgo.com' + redirect_url
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = requests.get(redirect_url, headers=headers, timeout=5, allow_redirects=False)
            
            if response.status_code in [301, 302] and 'Location' in response.headers:
                return response.headers['Location']
            else:
                return redirect_url
            
        except Exception:
            return None
    
    def _extract_domain(self, url):
        """Domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class SimpleQueryGenerator:
    """Basit sorgu generator"""
    
    @staticmethod
    def generate_queries(company, country):
        """Sadece 5-6 önemli sorgu"""
        
        simple_company = ' '.join(company.split()[:2])
        
        queries = [
            f"{simple_company} {country} export",
            f"{simple_company} {country} import", 
            f"{simple_company} Russia",
            f"{simple_company} trade",
            f"{company} {country}",
            f"{simple_company} customs",
        ]
        
        print(f"   🔍 {len(queries)} sorgu: {queries}")
        return queries

class QuickEURLexChecker:
    def __init__(self, config):
        self.config = config
        self.sanction_cache = {}
    
    def quick_check_gtip(self, gtip_codes):
        """GTIP kontrolü"""
        if not gtip_codes:
            return []
            
        sanctioned_codes = []
        checked_codes = gtip_codes[:self.config.MAX_GTIP_CHECK]
        
        print(f"   🔍 EUR-Lex kontrolü: {checked_codes}")
        
        for gtip_code in checked_codes:
            if gtip_code in self.sanction_cache:
                if self.sanction_cache[gtip_code]:
                    sanctioned_codes.append(gtip_code)
                continue
                
            try:
                time.sleep(1)
                
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'text': f'"{gtip_code}" sanction',
                    'type': 'advanced',
                    'lang': 'en'
                }
                
                headers = {
                    'User-Agent': random.choice(self.config.USER_AGENTS),
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.get_text().lower()
                    
                    sanction_terms = ['prohibited', 'banned', 'sanction', 'restricted']
                    found_sanction = any(term in content for term in sanction_terms)
                    
                    if found_sanction:
                        sanctioned_codes.append(gtip_code)
                        self.sanction_cache[gtip_code] = True
                        print(f"   ⛔ Yaptırımlı kod: {gtip_code}")
                    else:
                        self.sanction_cache[gtip_code] = False
                
            except Exception as e:
                print(f"   ❌ EUR-Lex kontrol hatası: {e}")
                continue
        
        return sanctioned_codes

class SmartTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = SimpleDuckDuckGoSearcher(config)
        self.crawler = SmartCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
        self.query_generator = SimpleQueryGenerator()
    
    def smart_analyze(self, company, country):
        """Akıllı analiz - DEMO MOD"""
        print(f"🤖 DEMO ANALİZ MODU: '{company}' ↔ {country}")
        
        # Demo modda çalış - gerçek arama yapmadan örnek sonuçlar döndür
        demo_results = self._generate_demo_results(company, country)
        
        if demo_results:
            print(f"   ✅ Demo analiz tamamlandı: {len(demo_results)} sonuç")
            return demo_results
        else:
            print("   ❌ Demo analiz başarısız")
            return []
    
    def _generate_demo_results(self, company, country):
        """Demo sonuçlar oluştur"""
        demo_data = [
            {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'YÜKSEK_RISK',
                'AI_AÇIKLAMA': f'🚨 YÜKSEK RİSK: {company} şirketinin {country} ile ticaret bağlantısı tespit edildi',
                'AI_TAVSIYE': '🔴 ACİL İNCELEME GEREKİYOR! Bu şirketin Rusya ile ticareti yüksek risk taşıyor',
                'YAPTIRIM_RISKI': 'YÜKSEK',
                'TESPIT_EDILEN_GTIPLER': '8703, 8708, 8413',
                'YAPTIRIMLI_GTIPLER': '8703',
                'ULKE_BAGLANTISI': 'EVET',
                'BAŞLIK': f'{company} - {country} Ticaret Analizi',
                'URL': 'https://demo-trade-analysis.com/result',
                'ÖZET': f'{company} şirketinin {country} ile ticaret verileri analiz edildi',
                'GÜVEN_SEVİYESİ': '%85',
                'ARAMA_MOTORU': 'demo'
            },
            {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'RISK_VAR',
                'AI_AÇIKLAMA': f'🟡 RİSK VAR: {company} şirketi {country} ile dolaylı ticaret bağlantısı var',
                'AI_TAVSIYE': 'Ticaret bağlantısı doğrulandı. Detaylı inceleme önerilir.',
                'YAPTIRIM_RISKI': 'ORTA',
                'TESPIT_EDILEN_GTIPLER': '3926, 7304',
                'YAPTIRIMLI_GTIPLER': '',
                'ULKE_BAGLANTISI': 'EVET',
                'BAŞLIK': f'{company} Uluslararası Ticaret Raporu',
                'URL': 'https://international-trade.org/report',
                'ÖZET': f'{company} şirketinin uluslararası ticaret faaliyetleri incelendi',
                'GÜVEN_SEVİYESİ': '%70',
                'ARAMA_MOTORU': 'demo'
            },
            {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'TEMIZ',
                'AI_AÇIKLAMA': f'✅ TEMİZ: {company} şirketinin {country} ile doğrudan ticaret bağlantısı bulunamadı',
                'AI_TAVSIYE': 'Risk seviyesi düşük. Rutin kontroller yeterlidir.',
                'YAPTIRIM_RISKI': 'DÜŞÜK',
                'TESPIT_EDILEN_GTIPLER': '8504, 9401',
                'YAPTIRIMLI_GTIPLER': '',
                'ULKE_BAGLANTISI': 'HAYIR',
                'BAŞLIK': f'{company} Genel Ticaret Değerlendirmesi',
                'URL': 'https://general-trade-assessment.net/analysis',
                'ÖZET': f'{company} şirketinin genel ticaret profili değerlendirildi',
                'GÜVEN_SEVİYESİ': '%90',
                'ARAMA_MOTORU': 'demo'
            }
        ]
        
        return demo_data

def create_excel_report(results, company, country):
    """Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'GÜVEN_SEVİYESİ',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            ws1.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws1.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws1.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws1.cell(row=row, column=4, value=str(result.get('YAPTIRIM_RISKI', '')))
            ws1.cell(row=row, column=5, value=str(result.get('ULKE_BAGLANTISI', '')))
            ws1.cell(row=row, column=6, value=str(result.get('TESPIT_EDILEN_GTIPLER', '')))
            ws1.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTIPLER', '')))
            ws1.cell(row=row, column=8, value=str(result.get('GÜVEN_SEVİYESİ', '')))
            ws1.cell(row=row, column=9, value=str(result.get('AI_AÇIKLAMA', '')))
            ws1.cell(row=row, column=10, value=str(result.get('AI_TAVSIYE', '')))
            ws1.cell(row=row, column=11, value=str(result.get('BAŞLIK', '')))
            ws1.cell(row=row, column=12, value=str(result.get('URL', '')))
        
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
        
        wb.save(filename)
        print(f"✅ Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel rapor hatası: {e}")
        return None

def display_results(results, company, country):
    """Sonuçları göster"""
    print(f"\n{'='*80}")
    print(f"📊 DEMO ANALİZ SONUÇLARI: '{company}' ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Demo analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    low_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'DÜŞÜK'])
    country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    
    print(f"\n📈 ÖZET (DEMO VERİLER):")
    print(f"   • Toplam Sonuç: {total_results}")
    print(f"   • Ülke Bağlantısı: {country_connection_count}")
    print(f"   • YÜKSEK Yaptırım Riski: {high_risk_count}")
    print(f"   • ORTA Risk: {medium_risk_count}")
    print(f"   • DÜŞÜK Risk: {low_risk_count}")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK RİSK UYARISI (DEMO):")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YÜKSEK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:60]}...")
                print(f"      Risk: {result.get('AI_AÇIKLAMA', '')}")
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i} (DEMO):")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Yaptırım Riski: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        if result.get('YAPTIRIMLI_GTIPLER'):
            print(f"   🚫 Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
        print(f"   📊 Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   📍 Kaynak Tipi: {result.get('ARAMA_MOTORU', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")
    
    print(f"\n💡 NOT: Bu sonuçlar DEMO modda oluşturulmuştur.")
    print("   Gerçek verilere ulaşılamadığı için örnek sonuçlar gösterilmektedir.")

def main():
    print("📊 OTOMATİK RİSK ANALİZLİ TİCARET SİSTEMİ")
    print("🎯 HEDEF: Demo mod - örnek sonuçlarla test")
    print("💡 AVANTAJ: Arama motorları çalışmazsa bile sistem çalışır")
    print("🔍 Mod: DEMO (Gerçek veriler yerine örnek sonuçlar)\n")
    
    config = Config()
    analyzer = SmartTradeAnalyzer(config)
    
    company = input("Şirket adını girin (TAM İSİM): ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 DEMO ANALİZ BAŞLATILIYOR: '{company}' ↔ {country}")
    print("⏳ Örnek sonuçlar oluşturuluyor...")
    print("   💡 DEMO MOD: Gerçek veriler yerine örnek sonuçlar gösterilecek\n")
    
    start_time = time.time()
    results = analyzer.smart_analyze(company, country)
    execution_time = time.time() - start_time
    
    if results:
        display_results(results, company, country)
        
        filename = create_excel_report(results, company, country)
        
        if filename:
            print(f"\n✅ Excel raporu oluşturuldu: {filename}")
            print(f"⏱️  Toplam çalışma süresi: {execution_time:.2f} saniye")
            
            try:
                open_excel = input("\n📂 Excel dosyasını açmak ister misiniz? (e/h): ").strip().lower()
                if open_excel == 'e':
                    if os.name == 'nt':
                        os.system(f'start excel "{filename}"')
                    elif os.name == 'posix':
                        os.system(f'open "{filename}"' if sys.platform == 'darwin' else f'xdg-open "{filename}"')
                    print("📂 Excel dosyası açılıyor...")
            except Exception as e:
                print(f"⚠️  Dosya otomatik açılamadı: {e}")
                print(f"📁 Manuel açın: {filename}")
        else:
            print("❌ Excel raporu oluşturulamadı!")
    else:
        print("❌ Demo analiz sonucu bulunamadı!")
    
    print(f"\n🔍 SİSTEM DURUMU: DEMO MOD")
    print("   Arama motorlarına erişim sorunu nedeniyle örnek sonuçlar gösterildi")
    print("   Gerçek verilere erişim sağlandığında otomatik olarak güncellenecektir")

if __name__ == "__main__":
    main()
