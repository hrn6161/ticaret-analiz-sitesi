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
from urllib.parse import urlparse
import concurrent.futures
import json

print("🚀 KAPSAMLI TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'comprehensive_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class AdvancedConfig:
    def __init__(self):
        self.MAX_RESULTS = 5
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 3
        self.MAX_GTIP_CHECK = 5
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        
        self.SEARCH_ENGINES = ["google", "duckduckgo", "bing"]
        self.TRADE_SITES = ["trademo.com", "eximpedia.app", "volza.com", "importyet.com"]

class MultiSearchEngine:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def search_all_engines(self, query):
        """Tüm arama motorlarında ara"""
        all_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_engine = {
                executor.submit(self._search_google, query): "google",
                executor.submit(self._search_duckduckgo, query): "duckduckgo", 
                executor.submit(self._search_bing, query): "bing"
            }
            
            for future in concurrent.futures.as_completed(future_to_engine):
                engine = future_to_engine[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    print(f"   ✅ {engine}: {len(results)} sonuç")
                except Exception as e:
                    print(f"   ❌ {engine} hatası: {e}")
        
        return all_results
    
    def _search_google(self, query):
        """Google araması"""
        try:
            url = "https://www.google.com/search"
            params = {"q": query, "num": self.config.MAX_RESULTS}
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = self.scraper.get(url, params=params, headers=headers, timeout=15)
            return self._parse_google_results(response.text)
        except Exception as e:
            print(f"   ❌ Google search error: {e}")
            return []
    
    def _parse_google_results(self, html):
        """Google sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for g in soup.find_all('div', class_='g'):
            try:
                title_elem = g.find('h3')
                if not title_elem:
                    continue
                
                title = title_elem.get_text()
                
                link_elem = g.find('a')
                url = link_elem.get('href') if link_elem else ""
                
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]
                
                snippet_elem = g.find('div', class_='VwiC3b')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                if url and url.startswith('http'):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'domain': self._extract_domain(url),
                        'search_engine': 'google'
                    })
            except Exception as e:
                continue
        
        return results
    
    def _search_duckduckgo(self, query):
        """DuckDuckGo araması"""
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': ''}
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            response = self.scraper.post(url, data=data, headers=headers, timeout=15)
            return self._parse_duckduckgo_results(response.text)
        except Exception as e:
            print(f"   ❌ DuckDuckGo search error: {e}")
            return []
    
    def _parse_duckduckgo_results(self, html):
        """DuckDuckGo sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for result in soup.find_all('div', class_='result'):
            try:
                title_elem = result.find('a', class_='result__a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text()
                url = title_elem.get('href')
                
                if url and '//duckduckgo.com/l/' in url:
                    try:
                        redirect_response = self.scraper.get(url, timeout=5, allow_redirects=True)
                        url = redirect_response.url
                    except:
                        pass
                
                snippet_elem = result.find('a', class_='result__snippet')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                if url and url.startswith('http'):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'domain': self._extract_domain(url),
                        'search_engine': 'duckduckgo'
                    })
            except Exception as e:
                continue
        
        return results
    
    def _search_bing(self, query):
        """Bing araması"""
        try:
            url = "https://www.bing.com/search"
            params = {"q": query, "count": self.config.MAX_RESULTS}
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = self.scraper.get(url, params=params, headers=headers, timeout=15)
            return self._parse_bing_results(response.text)
        except Exception as e:
            print(f"   ❌ Bing search error: {e}")
            return []
    
    def _parse_bing_results(self, html):
        """Bing sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for li in soup.find_all('li', class_='b_algo'):
            try:
                title_elem = li.find('h2')
                if not title_elem:
                    continue
                
                title = title_elem.get_text()
                
                link_elem = li.find('a')
                url = link_elem.get('href') if link_elem else ""
                
                snippet_elem = li.find('div', class_='b_caption')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                if url and url.startswith('http'):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'domain': self._extract_domain(url),
                        'search_engine': 'bing'
                    })
            except Exception as e:
                continue
        
        return results
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            return urlparse(url).netloc
        except:
            return ""

class AdvancedCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def crawl_with_retry(self, url, target_country):
        """Retry mekanizmalı crawl"""
        for attempt in range(self.config.RETRY_ATTEMPTS):
            try:
                result = self._smart_crawl(url, target_country)
                if result['status_code'] == 200:
                    return result
                
                print(f"   ⏰ Deneme {attempt + 1} başarısız, {2 ** attempt}s bekleniyor...")
                time.sleep(2 ** attempt)
                
            except Exception as e:
                print(f"   ❌ Crawl deneme {attempt + 1} hatası: {e}")
                time.sleep(2 ** attempt)
        
        return self._analyze_fallback(url, target_country)
    
    def _smart_crawl(self, url, target_country):
        """Akıllı crawl stratejisi"""
        domain = self._extract_domain(url)
        
        if any(trade_site in domain for trade_site in self.config.TRADE_SITES):
            return self._crawl_trade_site(url, target_country, domain)
        else:
            return self._crawl_general_site(url, target_country)
    
    def _crawl_trade_site(self, url, target_country, domain):
        """Ticaret siteleri için özel crawl"""
        headers = self._get_advanced_headers(domain)
        
        try:
            response = self.scraper.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                return self._parse_trade_site_content(response.text, target_country, domain, response.status_code)
            elif response.status_code == 403:
                print(f"   🔒 403 Forbidden: {domain}")
                return self._analyze_trade_site_fallback(url, target_country, domain)
            else:
                return {'country_found': False, 'gtip_codes': [], 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ Trade site crawl hatası: {e}")
            return self._analyze_trade_site_fallback(url, target_country, domain)
    
    def _crawl_general_site(self, url, target_country):
        """Genel siteler için crawl"""
        headers = self._get_advanced_headers()
        
        try:
            response = self.scraper.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._parse_general_content(response.text, target_country, response.status_code)
            else:
                return {'country_found': False, 'gtip_codes': [], 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ General site crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'status_code': 'ERROR'}
    
    def _get_advanced_headers(self, domain=None):
        """Gelişmiş headers"""
        headers = {
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if domain and 'trademo.com' in domain:
            headers.update({'Referer': 'https://www.trademo.com/'})
        elif domain and 'eximpedia.app' in domain:
            headers.update({'Referer': 'https://www.eximpedia.app/'})
        
        return headers
    
    def _parse_trade_site_content(self, html, target_country, domain, status_code):
        """Ticaret sitesi içeriğini parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        text_content = soup.get_text()
        text_lower = text_content.lower()
        
        country_found = self._advanced_country_detection(text_lower, target_country, domain)
        gtip_codes = self._advanced_gtip_extraction(text_content, domain)
        
        print(f"   🔍 {domain} analiz: Ülke={country_found}, GTIP={gtip_codes}")
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': text_content[:500] + "..." if len(text_content) > 500 else text_content,
            'status_code': status_code
        }
    
    def _parse_general_content(self, html, target_country, status_code):
        """Genel site içeriğini parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        text_content = soup.get_text()
        text_lower = text_content.lower()
        
        country_found = self._check_country_basic(text_lower, target_country)
        gtip_codes = self._extract_gtip_basic(text_content)
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': text_content[:300] + "..." if len(text_content) > 300 else text_content,
            'status_code': status_code
        }
    
    def _advanced_country_detection(self, text_lower, target_country, domain):
        """Gelişmiş ülke tespiti"""
        russia_patterns = ['russia', 'rusya', 'russian', 'rusian', 'rus']
        
        trade_context_patterns = [
            (r'export.*russia', 'export_russia'),
            (r'import.*russia', 'import_russia'),
            (r'destination.*russia', 'destination_russia'),
            (r'country of export.*russia', 'country_export_russia'),
        ]
        
        # Domain'e özel pattern'ler
        if 'eximpedia.app' in domain:
            if any(pattern in text_lower for pattern in ['destination russia', 'export russia']):
                print("   ✅ Eximpedia: Destination Russia tespit edildi")
                return True
                
        if 'trademo.com' in domain:
            if any(pattern in text_lower for pattern in ['country of export russia', 'export country russia']):
                print("   ✅ Trademo: Country of Export Russia tespit edildi")
                return True
        
        # Genel pattern kontrolü
        for pattern, context in trade_context_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                print(f"   ✅ Trade context bulundu: {context}")
                return True
        
        for country_pattern in russia_patterns:
            if country_pattern in text_lower:
                trade_terms = ['export', 'import', 'trade', 'shipment']
                for term in trade_terms:
                    if term in text_lower:
                        print(f"   ✅ Ülke+Trade bağlantısı: {country_pattern} + {term}")
                        return True
                return True
        
        return False
    
    def _advanced_gtip_extraction(self, text, domain):
        """Gelişmiş GTIP çıkarma"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\b\d{6}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
        ]
        
        codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    codes.add(code[:4])
                    print(f"   🔍 GTIP bulundu: {code[:4]}")
        
        # Otomatik 8708 ekleme
        if any(site in domain for site in self.config.TRADE_SITES):
            if any(keyword in text.lower() for keyword in ['vehicle', 'automotive', 'motor', '8708', '870830']):
                codes.add('8708')
                print("   🔍 Otomatik 8708 eklendi")
        
        return list(codes)
    
    def _check_country_basic(self, text_lower, target_country):
        """Temel ülke kontrolü"""
        return any(pattern in text_lower for pattern in ['russia', 'rusya', 'russian'])
    
    def _extract_gtip_basic(self, text):
        """Temel GTIP çıkarma"""
        matches = re.findall(r'\b\d{4}\b', text)
        return list(set(matches))
    
    def _analyze_trade_site_fallback(self, url, target_country, domain):
        """Ticaret sitesi fallback analizi"""
        url_lower = url.lower()
        
        country_found = 'russia' in url_lower or 'rusya' in url_lower
        gtip_found = '8708' in url_lower
        
        return {
            'country_found': country_found,
            'gtip_codes': ['8708'] if gtip_found else [],
            'status_code': 'URL_ANALYSIS'
        }
    
    def _analyze_fallback(self, url, target_country):
        """Genel fallback analizi"""
        return {
            'country_found': False,
            'gtip_codes': [],
            'status_code': 'FALLBACK'
        }
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            return urlparse(url).netloc
        except:
            return ""

class SanctionChecker:
    def __init__(self, config):
        self.config = config
        self.sanctioned_codes = {
            '8708': 'Motorlu taşıtlar yedek parçaları',
            '8711': 'Motorsikletler',
            '8703': 'Motorlu taşıtlar',
            '8408': 'Dizel motorlar',
        }
    
    def check_sanctions(self, gtip_codes):
        """Yaptırım kontrolü"""
        sanctioned = []
        reasons = []
        
        for code in gtip_codes[:self.config.MAX_GTIP_CHECK]:
            if code in self.sanctioned_codes:
                sanctioned.append(code)
                reasons.append(f"{code}: {self.sanctioned_codes[code]}")
        
        return sanctioned, reasons

class ComprehensiveTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = MultiSearchEngine(config)
        self.crawler = AdvancedCrawler(config)
        self.sanction_checker = SanctionChecker(config)
    
    def comprehensive_analyze(self, company, country):
        """Kapsamlı analiz"""
        print(f"🚀 KAPSAMLI ANALİZ: {company} ↔ {country}")
        
        queries = self._generate_comprehensive_queries(company, country)
        all_results = []
        
        # Paralel arama
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            search_futures = [executor.submit(self.searcher.search_all_engines, query) for query in queries]
            
            for future in concurrent.futures.as_completed(search_futures):
                try:
                    search_results = future.result()
                    for result in search_results:
                        if self._is_relevant_result(result, company, country):
                            analysis = self._analyze_single_result(result, company, country)
                            if analysis:
                                all_results.append(analysis)
                except Exception as e:
                    print(f"   ❌ Arama hatası: {e}")
        
        unique_results = self._remove_duplicates(all_results)
        return unique_results
    
    def _generate_comprehensive_queries(self, company, country):
        """Kapsamlı sorgular oluştur"""
        base_queries = [
            f'"{company}" "{country}" export',
            f'"{company}" "{country}" import',
            f'"{company}" "{country}" trade',
            f'"{company}" "{country}" shipment',
            f'"{company}" "{country}" supplier',
            f'"{company}" "{country}" HS code',
            f'"{company}" "{country}" GTIP',
        ]
        
        site_specific_queries = []
        for site in self.config.TRADE_SITES:
            site_specific_queries.extend([
                f'site:{site} "{company}"',
                f'site:{site} "{company}" {country}',
            ])
        
        return base_queries + site_specific_queries
    
    def _is_relevant_result(self, result, company, country):
        """Sonucun alakalı olup olmadığını kontrol et"""
        domain = result.get('domain', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        combined_text = f"{title} {snippet}"
        
        if any(trade_site in domain for trade_site in self.config.TRADE_SITES):
            return True
        
        if any(keyword in combined_text for keyword in [country.lower(), 'russia', 'rusya', '8708', 'hs code', 'gtip']):
            return True
        
        return False
    
    def _analyze_single_result(self, result, company, country):
        """Tekil sonucu analiz et"""
        try:
            crawl_result = self.crawler.crawl_with_retry(result['url'], country)
            
            sanctioned_gtips, sanction_reasons = self.sanction_checker.check_sanctions(crawl_result['gtip_codes'])
            
            confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
            
            analysis = self._create_comprehensive_analysis(
                company, country, result, crawl_result, sanctioned_gtips, sanction_reasons, confidence
            )
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Sonuç analiz hatası: {e}")
            return None
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        if any(trade_site in domain for trade_site in self.config.TRADE_SITES):
            confidence += 40
        
        if crawl_result['country_found']:
            confidence += 30
        
        if crawl_result['gtip_codes']:
            confidence += 20
        
        if sanctioned_gtips:
            confidence += 10
        
        return min(confidence, 100)
    
    def _create_comprehensive_analysis(self, company, country, search_result, crawl_result, sanctioned_gtips, sanction_reasons, confidence):
        """Kapsamlı analiz sonucu oluştur"""
        
        if sanctioned_gtips:
            status = "YÜKSEK_RISK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
            advice = f"⛔ ACİL DURUM! Yaptırımlı GTIP kodları: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif crawl_result['country_found'] and crawl_result['gtip_codes']:
            status = "ORTA_RISK"
            explanation = f"🟡 ORTA RİSK: {company} şirketinin {country} ile ticaret bağlantısı bulundu"
            advice = f"Ticaret bağlantısı doğrulandı. GTIP: {', '.join(crawl_result['gtip_codes'][:3])}"
            risk_level = "ORTA"
        elif crawl_result['country_found']:
            status = "DÜŞÜK_RISK"
            explanation = f"🟢 DÜŞÜK RİSK: {company} şirketinin {country} ile bağlantısı var"
            advice = "Ticaret bağlantısı bulundu ancak GTIP kodu tespit edilemedi"
            risk_level = "DÜŞÜK"
        else:
            status = "TEMIZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile ticaret bağlantısı bulunamadı"
            advice = "Risk tespit edilmedi"
            risk_level = "YOK"
        
        return {
            'ŞİRKET': company,
            'ÜLKE': country,
            'DURUM': status,
            'AI_AÇIKLAMA': explanation,
            'AI_TAVSIYE': advice,
            'YAPTIRIM_RISKI': risk_level,
            'TESPIT_EDILEN_GTIPLER': ', '.join(crawl_result['gtip_codes']),
            'YAPTIRIMLI_GTIPLER': ', '.join(sanctioned_gtips),
            'YAPTIRIM_NEDENLERI': ' | '.join(sanction_reasons),
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
            'BAŞLIK': search_result['title'],
            'URL': search_result['url'],
            'ÖZET': search_result['snippet'],
            'STATUS_CODE': crawl_result.get('status_code', 'N/A'),
            'KAYNAK_DOMAIN': search_result['domain'],
            'ARAMA_MOTORU': search_result.get('search_engine', 'N/A'),
            'GÜVEN_SEVİYESİ': f"%{confidence}",
            'İÇERİK_ÖNİZLEME': crawl_result.get('content_preview', '')[:200] + "..." if crawl_result.get('content_preview') else ''
        }
    
    def _remove_duplicates(self, results):
        """Benzersiz sonuçlar"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('URL', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results

def create_comprehensive_excel_report(results, company, country):
    """Kapsamlı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_kapsamlı_analiz.xlsx"
        
        wb = Workbook()
        
        # 1. Sayfa: Detaylı Sonuçlar
        ws1 = wb.active
        ws1.title = "Detaylı Analiz"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'YAPTIRIM_NEDENLERI',
            'GÜVEN_SEVİYESİ', 'KAYNAK_DOMAIN', 'ARAMA_MOTORU', 'STATUS_CODE',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET', 'İÇERİK_ÖNİZLEME'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            for col, key in enumerate(headers, 1):
                ws1.cell(row=row, column=col, value=str(result.get(key, '')))
        
        # 2. Sayfa: Özet
        ws2 = wb.create_sheet("Analiz Özeti")
        
        summary_data = [
            ["Şirket", company],
            ["Ülke", country],
            ["Analiz Tarihi", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Toplam Sonuç", len(results)],
            ["Yüksek Risk", len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])],
            ["Orta Risk", len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])],
            ["Düşük Risk", len([r for r in results if r.get('YAPTIRIM_RISKI') == 'DÜŞÜK'])],
            ["Temiz", len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YOK'])],
            ["Ülke Bağlantısı", len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])],
        ]
        
        for i, (label, value) in enumerate(summary_data, 1):
            ws2.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws2.cell(row=i, column=2, value=value)
        
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
        
        ws2.column_dimensions['A'].width = 20
        ws2.column_dimensions['B'].width = 30
        
        wb.save(filename)
        print(f"✅ Kapsamlı Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel rapor hatası: {e}")
        return None

def display_comprehensive_results(results, company, country):
    """Sonuçları detaylı göster"""
    print(f"\n{'='*100}")
    print(f"📊 KAPSAMLI ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*100}")
    
    if not results:
        print("❌ Hiçbir sonuç bulunamadı!")
        return
    
    # Özet istatistikler
    high_risk = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
    medium_risk = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    low_risk = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'DÜŞÜK'])
    clean = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YOK'])
    country_connections = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    
    print(f"\n📈 ÖZET İSTATİSTİKLER:")
    print(f"   • Toplam Sonuç: {len(results)}")
    print(f"   • YÜKSEK Risk: {high_risk}")
    print(f"   • ORTA Risk: {medium_risk}")
    print(f"   • DÜŞÜK Risk: {low_risk}")
    print(f"   • TEMİZ: {clean}")
    print(f"   • Ülke Bağlantısı: {country_connections}")
    
    if high_risk > 0:
        print(f"\n⚠️  KRİTİK YAPTIRIM UYARILARI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YÜKSEK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:70]}...")
                print(f"      🚫 Yaptırımlı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
                print(f"      📊 Güven: {result.get('GÜVEN_SEVİYESİ', '')}")
                print(f"      🌐 Kaynak: {result.get('KAYNAK_DOMAIN', '')}")
    
    # Detaylı sonuçlar
    for i, result in enumerate(results, 1):
        risk_color = "🔴" if result.get('YAPTIRIM_RISKI') == 'YÜKSEK' else "🟡" if result.get('YAPTIRIM_RISKI') == 'ORTA' else "🟢" if result.get('YAPTIRIM_RISKI') == 'DÜŞÜK' else "✅"
        
        print(f"\n{risk_color} SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Risk Seviyesi: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        
        if result.get('YAPTIRIMLI_GTIPLER'):
            print(f"   🚫 Yaptırımlı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
            print(f"   📋 Yaptırım Nedenleri: {result.get('YAPTIRIM_NEDENLERI', '')}")
        
        print(f"   📊 Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   🌐 Kaynak Domain: {result.get('KAYNAK_DOMAIN', 'N/A')}")
        print(f"   🔍 Arama Motoru: {result.get('ARAMA_MOTORU', 'N/A')}")
        print(f"   📋 Özet: {result.get('ÖZET', 'N/A')[:100]}...")
        print(f"   💡 AI Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 AI Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*80}")

def main():
    print("🚀 KAPSAMLI TİCARET ANALİZ SİSTEMİ")
    print("🎯 ÖZELLİKLER: Çoklu Arama Motoru + Paralel İşlem + Gelişmiş Pattern Matching")
    print("💡 HEDEF: Eximpedia Destination Russia ve Trademo Country of Export tespiti")
    print("📊 RAPOR: Detaylı Excel raporu ve kapsamlı analiz\n")
    
    config = AdvancedConfig()
    analyzer = ComprehensiveTradeAnalyzer(config)
    
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 KAPSAMLI ANALİZ BAŞLATILIYOR...")
    print("   ⚡ 3 arama motoru paralel çalışıyor...")
    print("   🔄 Retry mekanizması aktif...")
    print("   🎯 Gelişmiş pattern matching uygulanıyor...")
    print("   📊 Excel raporu hazırlanıyor...\n")
    
    start_time = time.time()
    
    results = analyzer.comprehensive_analyze(company, country)
    
    execution_time = time.time() - start_time
    
    # Sonuçları göster
    display_comprehensive_results(results, company, country)
    
    # Excel raporu oluştur
    excel_file = create_comprehensive_excel_report(results, company, country)
    
    print(f"\n⏱️  Toplam çalışma süresi: {execution_time:.2f} saniye")
    print(f"📊 Toplam sonuç: {len(results)}")
    
    if excel_file:
        print(f"📁 Excel raporu: {excel_file}")
        
        # Excel açma seçeneği
        try:
            open_excel = input("\n📂 Excel dosyasını açmak ister misiniz? (e/h): ").strip().lower()
            if open_excel == 'e':
                if os.name == 'nt':
                    os.system(f'start excel "{excel_file}"')
                elif os.name == 'posix':
                    os.system(f'open "{excel_file}"' if sys.platform == 'darwin' else f'xdg-open "{excel_file}"')
                print("📂 Excel dosyası açılıyor...")
        except Exception as e:
            print(f"⚠️  Dosya otomatik açılamadı: {e}")

if __name__ == "__main__":
    main()
