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

print("🚀 TAM ŞİRKET İSİMLİ GELİŞMİŞ TİCARET ANALİZ SİSTEMİ")

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
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

class AdvancedCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def advanced_crawl(self, url, target_country):
        """Gelişmiş crawl"""
        print(f"   🌐 Crawl: {url[:60]}...")
        
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = self.scraper.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                return self._parse_advanced_content(response.text, target_country, response.status_code)
            else:
                print(f"   ❌ Sayfa hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ Crawl hatası: {e}")
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
        
        trade_terms = ['export', 'import', 'country', 'origin', 'destination', 'trade', 'supplier', 'buyer']
        
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
            r'\bH.S\.\s?CODE\s?:?\s?(\d{4,8})\b',
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
    
    def analyze_snippet_deep(self, snippet_text, target_country, url=""):
        """Snippet analizi"""
        domain = self._extract_domain(url)
        combined_text = f"{snippet_text} {domain}".lower()
        
        country_found = self._check_country_advanced(combined_text, target_country)
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

class AdvancedDuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        print("   🦆 Gelişmiş DuckDuckGo arama motoru hazır!")
    
    def search_with_retry(self, query, max_results=10):
        """Gelişmiş DuckDuckGo arama - Retry mekanizmalı"""
        for attempt in range(2):
            try:
                print(f"   🔍 DuckDuckGo Search (Deneme {attempt+1}): {query}")
                
                wait_time = random.uniform(2, 4)
                time.sleep(wait_time)
                
                if attempt == 0:
                    results = self._search_method1(query, max_results)
                else:
                    results = self._search_method2(query, max_results)
                
                if results:
                    print(f"   ✅ DuckDuckGo {len(results)} sonuç buldu")
                    return results
                else:
                    print(f"   ⚠️ DuckDuckGo sonuç bulamadı (Deneme {attempt+1})")
                    
            except Exception as e:
                print(f"   ❌ DuckDuckGo hatası (Deneme {attempt+1}): {e}")
                continue
        
        return []
    
    def _search_method1(self, query, max_results):
        """İlk yöntem: HTML endpoint"""
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = self.scraper.post(url, data=data, headers=headers, timeout=15)
            return self._parse_html_results(response.text, max_results)
            
        except Exception as e:
            print(f"   ❌ Method1 hatası: {e}")
            return []
    
    def _search_method2(self, query, max_results):
        """İkinci yöntem: Lite endpoint"""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = self.scraper.get(url, headers=headers, timeout=15)
            return self._parse_lite_results(response.text, max_results)
            
        except Exception as e:
            print(f"   ❌ Method2 hatası: {e}")
            return []
    
    def _parse_html_results(self, html, max_results):
        """HTML sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Birden fazla olası selector
        selectors = [
            'div.result',
            'div.web-result',
            'div.result__body',
            'div.links_main'
        ]
        
        for selector in selectors:
            results_elements = soup.find_all('div', class_=selector)[:max_results]
            if results_elements:
                break
        
        for element in results_elements:
            try:
                title_elem = (element.find('a', class_='result__a') or 
                             element.find('a', class_='web-result__link') or
                             element.find('h2') or
                             element.find('a'))
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                
                # DuckDuckGo redirect linklerini çöz
                if url and ('//duckduckgo.com/l/' in url or url.startswith('/l/')):
                    url = self._resolve_redirect(url)
                    if not url:
                        continue
                
                snippet_elem = (element.find('a', class_='result__snippet') or
                               element.find('div', class_='result__snippet') or
                               element.find('div', class_='web-result__description') or
                               element.find('td', class_='result-snippet'))
                
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
                
                print(f"      📄 Bulundu: {title[:50]}...")
                
            except Exception as e:
                print(f"      ❌ Sonuç parse hatası: {e}")
                continue
        
        return results
    
    def _parse_lite_results(self, html, max_results):
        """Lite sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        tables = soup.find_all('table')
        
        for table in tables[:max_results]:
            try:
                links = table.find_all('a', href=True)
                for link in links:
                    title = link.get_text(strip=True)
                    url = link.get('href')
                    
                    if url and ('duckduckgo.com' not in url) and url.startswith('http'):
                        snippet = ""
                        next_row = table.find_next_sibling('tr')
                        if next_row:
                            snippet_cell = next_row.find('td')
                            if snippet_cell:
                                snippet = snippet_cell.get_text(strip=True)
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'full_text': f"{title} {snippet}",
                            'domain': self._extract_domain(url),
                            'search_engine': 'duckduckgo'
                        })
                        
                        print(f"      📄 Lite: {title[:50]}...")
                        break
                        
            except Exception as e:
                continue
        
        return results
    
    def _resolve_redirect(self, redirect_url):
        """Redirect URL'lerini çöz"""
        try:
            if redirect_url.startswith('/l/'):
                redirect_url = 'https://duckduckgo.com' + redirect_url
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = self.scraper.get(redirect_url, headers=headers, timeout=8, allow_redirects=True)
            return response.url
            
        except Exception as e:
            print(f"      ⚠️ Redirect çözme hatası: {e}")
            return None
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class ExactMatchQueryGenerator:
    """TAM ŞİRKET İSİMLİ sorgu generator"""
    
    @staticmethod
    def generate_queries(company, country):
        """TAM ŞİRKET İSMİ ile optimize edilmiş sorgular"""
        
        queries = []
        
        # TAM ŞİRKET İSMİ ile temel sorgular
        base_queries = [
            f'"{company}" "{country}"',  # Tırnak içinde tam eşleşme
            f'"{company}" {country} export',
            f'"{company}" {country} import',
            f'"{company}" {country} trade',
            f'"{company}" Russia',  # Rusya için özel
            f'"{company}" export Russia',
            f'"{company}" import Russia',
            f"{company} {country} export",  # Tırnaksız da deneyelim
            f"{company} {country} import",
            f"{company} {country} trade",
        ]
        
        # Ticaret verisi sorguları - TAM İSİM
        trade_queries = [
            f'"{company}" customs data',
            f'"{company}" trade data',
            f'"{company}" shipping',
            f'"{company}" supplier',
            f'"{company}" buyer',
            f'"{company}" HS code',
            f'"{company}" GTIP',
        ]
        
        # Platform özel sorguları - TAM İSİM
        platform_queries = [
            f'"{company}" site:trademo.com',
            f'"{company}" site:volza.com', 
            f'"{company}" site:eximpedia.app',
            f'"{company}" site:importyet.com',
            f'"{company}" site:exportgenius.in',
            f'"{company}" site:seair.co.in',
        ]
        
        # Tüm sorguları birleştir - TAM İSİM öncelikli
        queries.extend(base_queries)
        queries.extend(trade_queries)
        queries.extend(platform_queries)
        
        # Ek olarak tırnaksız sorgular da ekleyelim
        additional_queries = [
            f"{company} {country} business",
            f"{company} Russia business",
            f"{company} international trade",
            f"{company} overseas",
        ]
        
        queries.extend(additional_queries)
        
        print(f"   🔍 Oluşturulan TAM İSİMLİ sorgular: {queries[:5]}...")  # İlk 5'ini göster
        return queries

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
                wait_time = random.uniform(1, 2)
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
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.get_text().lower()
                    
                    sanction_terms = ['prohibited', 'banned', 'sanction', 'restricted', 'embargo']
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
        self.searcher = AdvancedDuckDuckGoSearcher(config)
        self.crawler = AdvancedCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
        self.query_generator = ExactMatchQueryGenerator()
    
    def enhanced_analyze(self, company, country):
        """Gelişmiş analiz - TAM ŞİRKET İSMİ ile"""
        print(f"🤖 TAM ŞİRKET İSİMLİ ANALİZ BAŞLATILIYOR: '{company}' ↔ {country}")
        
        # TAM ŞİRKET İSİMLİ sorgular oluştur
        search_queries = self.query_generator.generate_queries(company, country)
        
        all_results = []
        found_urls = set()
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"\n🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                if i > 1:
                    wait_time = random.uniform(3, 6)
                    print(f"   ⏳ Sorgular arası {wait_time:.1f}s bekleme...")
                    time.sleep(wait_time)
                
                search_results = self.searcher.search_with_retry(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    print(f"   ⚠️ Sonuç bulunamadı")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    if result['url'] in found_urls:
                        continue
                    
                    found_urls.add(result['url'])
                    
                    print(f"   📄 Sonuç {j}: {result['title'][:40]}...")
                    
                    # Şirket ismi kontrolü - TAM EŞLEŞME önemli
                    if self._check_company_match(result['full_text'], company):
                        print(f"   🎯 TAM ŞİRKET EŞLEŞMESİ: {company}")
                    
                    if j > 1:
                        time.sleep(random.uniform(1, 3))
                    
                    crawl_result = self.crawler.advanced_crawl(result['url'], country)
                    
                    # Snippet analizi ile destekle
                    if not crawl_result['country_found'] and not crawl_result['gtip_codes']:
                        snippet_analysis = self.crawler.analyze_snippet_deep(result['full_text'], country, result['url'])
                        if snippet_analysis['country_found'] or snippet_analysis['gtip_codes']:
                            crawl_result['country_found'] = snippet_analysis['country_found']
                            crawl_result['gtip_codes'] = snippet_analysis['gtip_codes']
                    
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'], result['full_text'], company)
                    
                    analysis = self.create_enhanced_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips, confidence
                    )
                    
                    all_results.append(analysis)
                    
                    # Yeterli sonuç bulduysak erken çık
                    if len(all_results) >= 8:
                        print("   🎯 Yeterli sonuç bulundu, analiz tamamlanıyor...")
                        return all_results
                
            except Exception as e:
                print(f"   ❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _check_company_match(self, text, company):
        """Şirket ismi tam eşleşme kontrolü"""
        text_lower = text.lower()
        company_lower = company.lower()
        
        # Tam şirket ismi geçiyor mu?
        if company_lower in text_lower:
            return True
        
        # Şirket isminin önemli kısımlarını kontrol et
        important_words = [word for word in company_lower.split() if len(word) > 3]
        if len(important_words) >= 2:
            match_count = sum(1 for word in important_words if word in text_lower)
            if match_count >= len(important_words) - 1:  # En az n-1 kelime eşleşmeli
                return True
        
        return False
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain, full_text, company):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # TAM ŞİRKET EŞLEŞMESİ - EN ÖNEMLİ
        if self._check_company_match(full_text, company):
            confidence += 40
        
        trusted_domains = ['trademo.com', 'eximpedia.app', 'volza.com', 'importyet.com', 'emis.com']
        if any(trusted in domain for trusted in trusted_domains):
            confidence += 30
        
        if crawl_result['gtip_codes']:
            confidence += 20
        
        if crawl_result['country_found']:
            confidence += 20
        
        if sanctioned_gtips:
            confidence += 10
        
        return min(confidence, 100)
    
    def create_enhanced_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips, confidence):
        """Gelişmiş analiz sonucu"""
        
        reasons = []
        if self._check_company_match(search_result['full_text'], company):
            reasons.append("TAM ŞİRKET EŞLEŞMESİ")
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
            'ARAMA_MOTORU': search_result.get('search_engine', 'duckduckgo')
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
    print(f"📊 TAM ŞİRKET İSİMLİ ANALİZ SONUÇLARI: '{company}' ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    exact_match_count = len([r for r in results if 'TAM ŞİRKET EŞLEŞMESİ' in r.get('NEDENLER', '')])
    
    print(f"\n📈 ÖZET:")
    print(f"   • Toplam Sonuç: {total_results}")
    print(f"   • TAM ŞİRKET EŞLEŞMESİ: {exact_match_count}")
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
    print("📊 TAM ŞİRKET İSİMLİ TİCARET ANALİZ SİSTEMİ")
    print("🎯 HEDEF: Tam şirket ismi ile kesin eşleşmeli analiz")
    print("💡 AVANTAJ: Sadece ilgili sonuçlar, yüksek doğruluk")
    print("🦆 Arama Motoru: DuckDuckGo\n")
    
    config = Config()
    analyzer = EnhancedTradeAnalyzer(config)
    
    company = input("Şirket adını girin (TAM İSİM): ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 TAM ŞİRKET İSİMLİ ANALİZ BAŞLATILIYOR: '{company}' ↔ {country}")
    print("⏳ DuckDuckGo ile TAM İSİM araması yapılıyor...")
    print("   Tırnak içinde sorgular oluşturuluyor...")
    print("   Tam eşleşme kontrolü yapılıyor...")
    print("   Sayfalar analiz ediliyor...\n")
    
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
