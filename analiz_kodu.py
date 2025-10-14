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

print("🚀 TAM FİRMA ADLI OTOMATİK RİSK ANALİZ SİSTEMİ")

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
        self.MAX_RESULTS = 15  # Artırıldı
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 5
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def smart_crawl(self, url, target_country):
        """Akıllı crawl - snippet analizi öncelikli"""
        print(f"   🌐 Crawl: {url[:60]}...")
        
        # ÖNCE SNIPPET ANALİZİ - daha hızlı ve güvenilir
        time.sleep(0.5)  # Kısa bekleme
        
        # Cloudscraper ile dene
        result = self._try_cloudscraper(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # Normal requests ile dene
        result = self._try_requests(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # Her ikisi de başarısızsa snippet analizi döndür
        print(f"   🔍 Sayfa erişilemiyor, snippet analizi kullanılıyor...")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'BLOCKED'}
    
    def _try_cloudscraper(self, url, target_country):
        """Cloudscraper ile dene"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.scraper.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Cloudscraper başarılı: {url}")
                return self._parse_content(response.text, target_country, response.status_code)
            else:
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
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Requests başarılı: {url}")
                return self._parse_content(response.text, target_country, response.status_code)
            else:
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
        """Ülke kontrolü - daha geniş varyasyonlar"""
        country_variations = [
            target_country.lower(),
            'russia', 'rusya', 'russian', 'rus', 'rossiya',
            'moscow', 'moskova', 'saint petersburg', 'st petersburg'
        ]
        
        for country_var in country_variations:
            if country_var in text_lower:
                return True
        
        return False
    
    def extract_gtip_codes(self, text):
        """GTIP kod çıkarma - geliştirilmiş"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\b\d{6}\b',
            r'\b\d{8}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?Code\s?:?\s?(\d{4,8})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4 and len(code) <= 8:
                    all_codes.add(code[:4])  # İlk 4 hane
        
        return list(all_codes)

class SimpleDuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        print("   🦆 DuckDuckGo arama motoru hazır!")
    
    def search_simple(self, query, max_results=15):
        """Basit DuckDuckGo arama - geliştirilmiş"""
        try:
            print(f"   🔍 Arama: {query}")
            
            time.sleep(random.uniform(2, 4))  # Rastgele bekleme
            
            url = "https://html.duckduckgo.com/html/"
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://html.duckduckgo.com',
                'Connection': 'keep-alive',
            }
            
            response = self.scraper.post(url, data=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                results = self._parse_results(response.text, max_results)
                print(f"   ✅ {len(results)} sonuç buldu")
                return results
            else:
                print(f"   ❌ Arama hatası {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Arama hatası: {e}")
            return []
    
    def _parse_results(self, html, max_results):
        """Sonuç parsing - geliştirilmiş"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Farklı result class'larını dene
        results_elements = soup.find_all('div', class_=['result', 'result__body', 'web-result'])
        
        for element in results_elements[:max_results]:
            try:
                title_elem = element.find('a', class_=['result__a', 'result__url'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                
                # Redirect çöz
                if url and ('//duckduckgo.com/l/' in url or url.startswith('/l/')):
                    url = self._resolve_redirect(url)
                    if not url:
                        continue
                
                snippet_elem = element.find(attrs={'class': ['result__snippet', 'result-snippet']})
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if url and url.startswith('//'):
                    url = 'https:' + url
                
                if not url or not url.startswith('http'):
                    continue
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'full_text': f"{title} {snippet}",
                    'domain': self._extract_domain(url),
                    'search_engine': 'duckduckgo'
                })
                
                print(f"      📄 {title[:50]}...")
                
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
            
            response = self.scraper.get(redirect_url, headers=headers, timeout=5, allow_redirects=True)
            return response.url
            
        except Exception:
            return None
    
    def _extract_domain(self, url):
        """Domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class ExactQueryGenerator:
    """TAM FİRMA ADLI sorgu generator - TIRNAK YOK"""
    
    @staticmethod
    def generate_queries(company, country):
        """TAM FİRMA ADI ile 10 sorgu - TIRNAK YOK"""
        
        queries = [
            # TAM FİRMA ADI ile ülke bağlantılı sorgular - TIRNAK YOK
            f"{company} {country} export",
            f"{company} {country} import", 
            f"{company} {country}",
            f"{company} Russia",
            f"{company} {country} trade",
            f"{company} {country} customs",
            f"{company} {country} shipment",
            f"{company} {country} logistics",
            # SADECE FİRMA ADI ile genel aramalar - TIRNAK YOK
            f"{company}",
            f"{company} company"
        ]
        
        print(f"   🔍 TAM FİRMA ADI ile {len(queries)} sorgu oluşturuldu (TIRNAK YOK)")
        return queries

class QuickEURLexChecker:
    def __init__(self, config):
        self.config = config
        self.sanction_cache = {}
    
    def quick_check_gtip(self, gtip_codes):
        """GTIP kontrolü - geliştirilmiş"""
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
                
                # Çoklu arama terimleri
                search_terms = [
                    f'"{gtip_code}" sanction Russia',
                    f'"{gtip_code}" prohibited Russia', 
                    f'"{gtip_code}" ban Russia',
                    f'HS code {gtip_code} Russia sanction'
                ]
                
                for search_term in search_terms:
                    url = "https://eur-lex.europa.eu/search.html"
                    params = {
                        'text': search_term,
                        'type': 'advanced',
                        'lang': 'en'
                    }
                    
                    headers = {
                        'User-Agent': random.choice(self.config.USER_AGENTS),
                    }
                    
                    response = requests.get(url, params=params, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        content = soup.get_text().lower()
                        
                        sanction_terms = ['prohibited', 'banned', 'sanction', 'restricted', 'embargo']
                        found_sanction = any(term in content for term in sanction_terms)
                        
                        if found_sanction:
                            sanctioned_codes.append(gtip_code)
                            self.sanction_cache[gtip_code] = True
                            print(f"   ⛔ Yaptırımlı kod: {gtip_code}")
                            break
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
        self.query_generator = ExactQueryGenerator()
    
    def smart_analyze(self, company, country):
        """Akıllı analiz - TAM FİRMA ADI ile - OPTİMİZE EDİLMİŞ"""
        print(f"🤖 TAM FİRMA ADLI ANALİZ: '{company}' ↔ {country}")
        
        search_queries = self.query_generator.generate_queries(company, country)
        
        all_results = []
        found_urls = set()
        country_connection_found = False
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"\n🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                if i > 1:
                    wait_time = random.uniform(3, 6)
                    print(f"   ⏳ {wait_time:.1f}s bekleme...")
                    time.sleep(wait_time)
                
                search_results = self.searcher.search_simple(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    print(f"   ⚠️ Sonuç bulunamadı: {query}")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    if result['url'] in found_urls:
                        continue
                    
                    found_urls.add(result['url'])
                    
                    print(f"   📄 Sonuç {j}: {result['title'][:40]}...")
                    
                    if j > 1:
                        time.sleep(random.uniform(1, 2))
                    
                    # ÖNCE SNIPPET ANALİZİ - daha hızlı
                    snippet_analysis = self._analyze_snippet(result['full_text'], country, result['url'])
                    
                    # Sayfa crawl denemesi
                    crawl_result = self.crawler.smart_crawl(result['url'], country)
                    
                    # Eğer crawl başarısızsa snippet kullan
                    if crawl_result['status_code'] != 200:
                        crawl_result['country_found'] = snippet_analysis['country_found']
                        crawl_result['gtip_codes'] = snippet_analysis['gtip_codes']
                        print(f"   🔍 Snippet analizi kullanıldı: Ülke={snippet_analysis['country_found']}, GTIP={snippet_analysis['gtip_codes']}")
                    else:
                        # Crawl başarılıysa, snippet ile birleştir
                        if snippet_analysis['country_found']:
                            crawl_result['country_found'] = True
                        if snippet_analysis['gtip_codes']:
                            crawl_result['gtip_codes'] = list(set(crawl_result['gtip_codes'] + snippet_analysis['gtip_codes']))
                    
                    # Ülke bağlantısı tespit edildi mi?
                    if crawl_result['country_found']:
                        country_connection_found = True
                        print(f"   🚨 ÜLKE BAĞLANTISI TESPİT EDİLDİ: {company} ↔ {country}")
                    
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
                    
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips, confidence, country_connection_found
                    )
                    
                    all_results.append(analysis)
                    
                    if len(all_results) >= 8:  # Daha fazla sonuç
                        print("   🎯 8 sonuç bulundu, analiz tamamlanıyor...")
                        return all_results
                
            except Exception as e:
                print(f"   ❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _analyze_snippet(self, snippet_text, target_country, url=""):
        """Snippet analizi - GELİŞTİRİLMİŞ"""
        domain = self._extract_domain(url)
        combined_text = f"{snippet_text} {domain}".lower()
        
        country_found = self._check_country_snippet(combined_text, target_country)
        gtip_codes = self._extract_gtip_snippet(snippet_text)
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes
        }
    
    def _check_country_snippet(self, text_lower, target_country):
        """Snippet ülke kontrolü - genişletilmiş"""
        country_variations = [
            target_country.lower(),
            'russia', 'rusya', 'russian', 'rus', 'rossiya',
            'moscow', 'moskova', 'saint petersburg', 'st petersburg'
        ]
        
        for country_var in country_variations:
            if country_var in text_lower:
                return True
        
        return False
    
    def _extract_gtip_snippet(self, text):
        """Snippet GTIP çıkarma - geliştirilmiş"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\b\d{6}\b',
            r'\b\d{8}\b',
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
                if len(code) >= 4 and len(code) <= 8:
                    all_codes.add(code[:4])
        
        return list(all_codes)
    
    def _extract_domain(self, url):
        """Domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi - iyileştirilmiş"""
        confidence = 0
        
        if crawl_result['country_found']:
            confidence += 40
        
        if crawl_result['gtip_codes']:
            confidence += 30
        
        if sanctioned_gtips:
            confidence += 30
        
        # Domain güvenilirliği
        trusted_domains = ['eximpedia', 'trademo', 'volza', 'exportgenius', 'comtrade']
        if any(trusted in domain.lower() for trusted in trusted_domains):
            confidence += 20
        
        return min(confidence, 100)
    
    def create_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips, confidence, country_connection_found):
        """Analiz sonucu - GELİŞTİRİLMİŞ"""
        
        # OTOMATİK RİSK BELİRLEME
        if country_connection_found and sanctioned_gtips:
            status = "KRİTİK_RİSK"
            explanation = f"🚨 KRİTİK RİSK: {company} şirketi {country} ile YASAKLI ürün ticareti yapıyor"
            ai_tavsiye = f"🔴 ACİL DURUM! {company} şirketi {country} ile yasaklı GTIP kodlarıyla ticaret yapıyor: {', '.join(sanctioned_gtips)}"
            risk_level = "KRİTİK"
        elif country_connection_found:
            status = "YÜKSEK_RISK"
            explanation = f"🚨 YÜKSEK RİSK: {company} şirketinin {country} ile ticaret bağlantısı bulundu"
            ai_tavsiye = f"🔴 ACİL İNCELEME GEREKİYOR! {company} şirketi {country} ile ticaret yapıyor"
            risk_level = "YÜKSEK"
        elif sanctioned_gtips:
            status = "YAPTIRIMLI_RISK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi yaptırımlı ürünlerle ticaret yapıyor"
            ai_tavsiye = f"⛔ DİKKAT! Bu ürünlerin {country.upper()} ihracı yasak: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif crawl_result['country_found'] and crawl_result['gtip_codes']:
            status = "RISK_VAR"
            explanation = f"🟡 RİSK VAR: {company} şirketi {country} ile ticaret bağlantısı bulundu"
            ai_tavsiye = f"Ticaret bağlantısı doğrulandı. GTIP kodları: {', '.join(crawl_result['gtip_codes'][:3])}"
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
            'TESPIT_EDILEN_GTIPLER': ', '.join(crawl_result['gtip_codes'][:5]),
            'YAPTIRIMLI_GTIPLER': ', '.join(sanctioned_gtips),
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
            'BAŞLIK': search_result['title'],
            'URL': search_result['url'],
            'ÖZET': search_result['snippet'],
            'GÜVEN_SEVİYESİ': f"%{confidence}",
            'ARAMA_MOTORU': 'duckduckgo',
            'KAYNAK_TIPI': 'SNIPPET' if crawl_result['status_code'] != 200 else 'FULL_PAGE'
        }

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
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'KAYNAK_TIPI'
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
            ws1.cell(row=row, column=13, value=str(result.get('KAYNAK_TIPI', '')))
        
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
    print(f"📊 TAM FİRMA ADLI ANALİZ SONUÇLARI: '{company}' ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') in ['YÜKSEK', 'KRİTİK']])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    snippet_count = len([r for r in results if r.get('KAYNAK_TIPI') == 'SNIPPET'])
    
    print(f"\n📈 ÖZET:")
    print(f"   • Toplam Sonuç: {total_results}")
    print(f"   • Ülke Bağlantısı: {country_connection_count}")
    print(f"   • YÜKSEK/KRİTİK Yaptırım Riski: {high_risk_count}")
    print(f"   • ORTA Risk: {medium_risk_count}")
    print(f"   • Snippet Analizi: {snippet_count}")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK RİSK UYARISI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') in ['YÜKSEK', 'KRİTİK']:
                print(f"   🔴 {result.get('BAŞLIK', '')[:60]}...")
                print(f"      Risk: {result.get('AI_AÇIKLAMA', '')}")
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Yaptırım Riski: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        if result.get('YAPTIRIMLI_GTIPLER'):
            print(f"   🚫 Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
        print(f"   📊 Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   📍 Kaynak Tipi: {result.get('KAYNAK_TIPI', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 TAM FİRMA ADLI OTOMATİK RİSK ANALİZ SİSTEMİ")
    print("🎯 HEDEF: TAM firma adı ile doğru sonuçlar")
    print("💡 AVANTAJ: Kısaltma YOK, 10 sorgu, snippet analizi öncelikli")
    print("🦆 Arama Motoru: DuckDuckGo\n")
    
    config = Config()
    analyzer = SmartTradeAnalyzer(config)
    
    company = input("Şirket adını girin (TAM İSİM): ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 TAM FİRMA ADLI ANALİZ BAŞLATILIYOR: '{company}' ↔ {country}")
    print("⏳ TAM firma adı ile 10 sorgu yapılıyor...")
    print("   Kısaltma YOK, doğru şirket aranıyor...")
    print("   TIRNAK YOK, normal arama yapılıyor...")
    print("   Snippet analizi öncelikli, daha hızlı sonuç...\n")
    
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
        print("❌ Analiz sonucu bulunamadı!")

if __name__ == "__main__":
    main()
