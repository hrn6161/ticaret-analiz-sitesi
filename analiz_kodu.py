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
import json

print("🚀 DUCKDUCKGO ANA, GOOGLE FALLBACK İLE TİCARET ANALİZ SİSTEMİ")

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
        self.MAX_RESULTS = 5
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class AdvancedCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def advanced_crawl(self, url, target_country):
        """Gelişmiş crawl"""
        print(f"   🌐 Crawl: {url[:60]}...")
        
        domain = self._extract_domain(url)
        if any(site in domain for site in ['trademo.com', 'volza.com', 'eximpedia.app']):
            wait_time = random.uniform(8, 12)
            print(f"   ⏳ {domain} için {wait_time:.1f}s bekleme...")
            time.sleep(wait_time)
        
        page_result = self._try_cloudscraper_crawl(url, target_country)
        if page_result['status_code'] == 200:
            return page_result
        
        page_result = self._try_page_crawl(url, target_country)
        if page_result['status_code'] == 200:
            return page_result
        
        print(f"   🔍 Snippet analizi: {url}")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'SNIPPET_ANALYSIS'}
    
    def _try_cloudscraper_crawl(self, url, target_country):
        """Cloudscraper ile crawl"""
        try:
            print(f"   ☁️ Cloudscraper: {url}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = self.scraper.get(url, headers=headers, timeout=25)
            
            if response.status_code == 200:
                print(f"   ✅ Cloudscraper başarılı: {url}")
                return self._parse_advanced_content(response.text, target_country, response.status_code)
            else:
                print(f"   ❌ Cloudscraper hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
        except Exception as e:
            print(f"   ❌ Cloudscraper hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'CLOUDSCRAPER_ERROR'}
    
    def _try_page_crawl(self, url, target_country):
        """Normal requests ile crawl"""
        try:
            print(f"   🌐 Normal requests: {url}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                print(f"   ✅ Normal requests başarılı: {url}")
                return self._parse_advanced_content(response.text, target_country, response.status_code)
            elif response.status_code == 403:
                print(f"   🔒 403 Forbidden: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 403}
            else:
                print(f"   ❌ Sayfa hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
        except Exception as e:
            print(f"   ❌ Sayfa crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_advanced_content(self, html, target_country, status_code):
        """İçerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            country_found = self._check_country_advanced(text_lower, target_country)
            gtip_codes = self.extract_advanced_gtip_codes(text_content)
            
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
    
    def _check_country_advanced(self, text_lower, target_country):
        """Ülke kontrolü"""
        country_variations = [
            target_country.lower(),
            target_country.upper(), 
            target_country.title(),
            'russia', 'rusya', 'rusian', 'rus'
        ]
        
        trade_terms = ['export', 'import', 'country', 'origin', 'destination', 'trade']
        
        for country_var in country_variations:
            if country_var in text_lower:
                for term in trade_terms:
                    if f"{term} {country_var}" in text_lower or f"{country_var} {term}" in text_lower:
                        return True
                return True
        
        return False
    
    def extract_advanced_gtip_codes(self, text):
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
    
    def analyze_snippet_deep(self, snippet_text, target_country):
        """Snippet analizi"""
        if not snippet_text:
            return {'country_found': False, 'gtip_codes': []}
        
        text_lower = snippet_text.lower()
        
        country_found = self._check_country_advanced(text_lower, target_country)
        gtip_codes = self.extract_advanced_gtip_codes(snippet_text)
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes
        }
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class GoogleSearcher:
    def __init__(self, config):
        self.config = config
        # GOOGLE API CREDENTIALS
        self.google_api_key = "AIzaSyC2A3ANshAolgr4hNNlFOtgNSlcQtIP40Y"
        self.google_cse_id = "d65dec7934a544da1"
        
        print(f"   🔑 Google API Key: {self.google_api_key[:10]}...")
        print(f"   🔍 Google CSE ID: {self.google_cse_id}")
        print("   ✅ Google Custom Search API hazır!")
    
    def google_search(self, query, max_results=5):
        """Google Custom Search API ile arama - Gelişmiş hata yönetimi"""
        try:
            print(f"   🔍 Google Search: {query}")
            
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)
            
            endpoint = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': min(max_results, 10)
            }
            
            print(f"   🌐 Google API isteği: {query}")
            response = requests.get(endpoint, params=params, timeout=10)
            
            # Response tipini kontrol et
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' not in content_type:
                print(f"   ❌ Google API JSON yerine HTML döndürdü: {content_type}")
                print(f"   ❌ Response ilk 200 karakter: {response.text[:200]}")
                return []
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results = self.parse_google_results(data)
                    print(f"   ✅ Google {len(results)} sonuç buldu")
                    return results
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode hatası: {e}")
                    print(f"   ❌ Response: {response.text[:500]}")
                    return []
            else:
                print(f"   ❌ Google API hatası {response.status_code}: {response.text[:200]}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Google API bağlantı hatası: {e}")
            return []
        except Exception as e:
            print(f"   ❌ Google arama hatası: {e}")
            return []
    
    def parse_google_results(self, data):
        """Google sonuçlarını parse et"""
        results = []
        
        if 'items' in data:
            for item in data['items']:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'full_text': f"{item.get('title', '')} {item.get('snippet', '')}",
                    'domain': self._extract_domain(item.get('link', '')),
                    'search_engine': 'google'
                })
                
                print(f"      📄 Google: {item.get('title', '')[:50]}...")
                print(f"      🌐 URL: {item.get('link', '')[:80]}...")
        
        return results
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class DuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
    
    def duckduckgo_search(self, query, max_results=5):
        """DuckDuckGo arama - Ana yöntem olarak"""
        try:
            print(f"   🔍 DuckDuckGo Search: {query}")
            
            wait_time = random.uniform(3, 5)
            time.sleep(wait_time)
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': '', 'kl': 'us-en'}
            
            scraper = cloudscraper.create_scraper()
            response = scraper.post(url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                results = self.parse_duckduckgo_results(response.text, max_results)
                print(f"   ✅ DuckDuckGo {len(results)} sonuç buldu")
                return results
            else:
                print(f"   ❌ DuckDuckGo hatası {response.status_code}")
                return []
        except Exception as e:
            print(f"   ❌ DuckDuckGo arama hatası: {e}")
            return []
    
    def parse_duckduckgo_results(self, html, max_results):
        """DuckDuckGo sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for div in soup.find_all('div', class_='result')[:max_results]:
            try:
                title_elem = div.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                
                # Redirect handling
                if url and '//duckduckgo.com/l/' in url:
                    try:
                        time.sleep(1)
                        scraper = cloudscraper.create_scraper()
                        redirect_response = scraper.get(url, timeout=8, allow_redirects=True)
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
                    'full_text': f"{title} {snippet}",
                    'domain': self._extract_domain(url),
                    'search_engine': 'duckduckgo'
                })
                
                print(f"      📄 DuckDuckGo: {title[:50]}...")
                
            except Exception as e:
                print(f"      ❌ DuckDuckGo sonuç parse hatası: {e}")
                continue
        
        return results
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class EnhancedSearcher:
    def __init__(self, config):
        self.config = config
        self.google_searcher = GoogleSearcher(config)
        self.ddg_searcher = DuckDuckGoSearcher(config)
    
    def enhanced_search(self, query, max_results=5):
        """Akıllı arama - DuckDuckGo ana, Google fallback"""
        
        # Önce DuckDuckGo ile dene (daha güvenilir)
        ddg_results = self.ddg_searcher.duckduckgo_search(query, max_results)
        if ddg_results:
            return ddg_results
        
        # DuckDuckGo başarısızsa Google fallback
        print("   🔄 DuckDuckGo sonuç vermedi, Google deneniyor...")
        google_results = self.google_searcher.google_search(query, max_results)
        return google_results

class QuickEURLexChecker:
    def __init__(self, config):
        self.config = config
        self.sanction_cache = {}
    
    def quick_check_gtip(self, gtip_codes):
        """Hızlı GTIP kontrolü"""
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
                wait_time = random.uniform(2, 4)
                time.sleep(wait_time)
                
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'text': f'"{gtip_code}" sanction prohibited',
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

class EnhancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = EnhancedSearcher(config)
        self.crawler = AdvancedCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
    
    def enhanced_analyze(self, company, country):
        """Gelişmiş analiz - DuckDuckGo ana, Google fallback"""
        print(f"🤖 DUCKDUCKGO ANA, GOOGLE FALLBACK İLE ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} trade",
            f"{company} {country} export", 
            f"{company} trade data",
            f"{company} {country} business",
            f"{company} {country} import export",
            f'"{company}" "{country}"',
            f"{company} {country} customs data"
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"\n🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                if i > 1:
                    wait_time = random.uniform(8, 12)
                    print(f"   ⏳ Sorgular arası {wait_time:.1f}s bekleme...")
                    time.sleep(wait_time)
                
                search_results = self.searcher.enhanced_search(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    print(f"   ⚠️ Sonuç bulunamadı")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    print(f"   📄 Sonuç {j}: {result['title'][:40]}...")
                    
                    if j > 1:
                        wait_time = random.uniform(4, 6)
                        time.sleep(wait_time)
                    
                    crawl_result = self.crawler.advanced_crawl(result['url'], country)
                    
                    if crawl_result['status_code'] != 200:
                        snippet_analysis = self.crawler.analyze_snippet_deep(result['full_text'], country)
                        if snippet_analysis['country_found'] or snippet_analysis['gtip_codes']:
                            crawl_result['country_found'] = snippet_analysis['country_found']
                            crawl_result['gtip_codes'] = snippet_analysis['gtip_codes']
                    
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
                    
                    analysis = self.create_enhanced_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips, confidence
                    )
                    
                    all_results.append(analysis)
                
            except Exception as e:
                print(f"   ❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        trusted_domains = ['trademo.com', 'eximpedia.app', 'volza.com', 'importyet.com', 'emis.com']
        if any(trusted in domain for trusted in trusted_domains):
            confidence += 30
        
        if crawl_result['gtip_codes']:
            confidence += 25
        
        if crawl_result['country_found']:
            confidence += 25
        
        if sanctioned_gtips:
            confidence += 20
        
        return min(confidence, 100)
    
    def create_enhanced_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips, confidence):
        """Gelişmiş analiz sonucu"""
        
        reasons = []
        if crawl_result['country_found']:
            reasons.append("Ülke bağlantısı tespit edildi")
        if crawl_result['gtip_codes']:
            reasons.append(f"GTIP kodları bulundu: {', '.join(crawl_result['gtip_codes'][:3])}")
        if sanctioned_gtips:
            reasons.append(f"Yaptırımlı GTIP kodları: {', '.join(sanctioned_gtips)}")
        if any(trusted in search_result['domain'] for trusted in ['trademo.com', 'volza.com', 'eximpedia.app']):
            reasons.append("Güvenilir ticaret verisi kaynağı")
        
        if sanctioned_gtips:
            status = "YAPTIRIMLI_YÜKSEK_RISK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
            ai_tavsiye = f"⛔ ACİL DURUM! Bu ürünlerin {country.upper()} ihracı YASAKTIR: {', '.join(sanctioned_gtips)}"
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
            'STATUS_CODE': crawl_result.get('status_code', 'N/A'),
            'KAYNAK_URL': search_result['url'],
            'GÜVEN_SEVİYESİ': f"%{confidence}",
            'NEDENLER': ' | '.join(reasons) if reasons else 'Belirsiz',
            'ARAMA_MOTORU': search_result.get('search_engine', 'bilinmiyor')
        }

def create_detailed_excel_report(results, company, country):
    """Detaylı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'GÜVEN_SEVİYESİ', 'NEDENLER',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET', 'ARAMA_MOTORU'
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
            ws1.cell(row=row, column=9, value=str(result.get('NEDENLER', '')))
            ws1.cell(row=row, column=10, value=str(result.get('AI_AÇIKLAMA', '')))
            ws1.cell(row=row, column=11, value=str(result.get('AI_TAVSIYE', '')))
            ws1.cell(row=row, column=12, value=str(result.get('BAŞLIK', '')))
            ws1.cell(row=row, column=13, value=str(result.get('URL', '')))
            ws1.cell(row=row, column=14, value=str(result.get('ÖZET', '')))
            ws1.cell(row=row, column=15, value=str(result.get('ARAMA_MOTORU', '')))
        
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
    print(f"📊 DUCKDUCKGO ANA, GOOGLE FALLBACK ANALİZ SONUÇLARI: {company} ↔ {country}")
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
        print(f"   🔍 Arama Motoru: {result.get('ARAMA_MOTORU', 'N/A')}")
        print(f"   📋 Nedenler: {result.get('NEDENLER', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 DUCKDUCKGO ANA, GOOGLE FALLBACK İLE TİCARET ANALİZ SİSTEMİ")
    print("🎯 HEDEF: DuckDuckGo ile güvenilir, Google fallback ile yedekli analiz")
    print("💡 AVANTAJ: JSON hatalarından kaçınma, kesintisiz çalışma")
    print("🔑 Google API Key: AIzaSyC2A3ANshAolgr4hNNlFOtgNSlcQtIP40Y")
    print("🔍 Google CSE ID: d65dec7934a544da1")
    print("🦆 Ana Arama: DuckDuckGo\n")
    
    config = Config()
    analyzer = EnhancedTradeAnalyzer(config)
    
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 DUCKDUCKGO ANA, GOOGLE FALLBACK ANALİZİ BAŞLATILIYOR: {company} ↔ {country}")
    print("⏳ DuckDuckGo ile arama yapılıyor...")
    print("   Google API fallback hazır...")
    print("   Sayfalar analiz ediliyor...")
    print("   GTIP kodları taranıyor...")
    print("   Yaptırım kontrolü yapılıyor...\n")
    
    start_time = time.time()
    results = analyzer.enhanced_analyze(company, country)
    execution_time = time.time() - start_time
    
    if results:
        display_results(results, company, country)
        
        filename = create_detailed_excel_report(results, company, country)
        
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
