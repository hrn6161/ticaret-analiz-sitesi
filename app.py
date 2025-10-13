from flask import Flask, request, jsonify, render_template, send_file
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

app = Flask(__name__)

print("🚀 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]

class AdvancedCrawler:
    def __init__(self, config):
        self.config = config
        # Cloudscraper ile bot koruması aşma
        self.scraper = cloudscraper.create_scraper()
    
    def advanced_crawl(self, url, target_country):
        """Gelişmiş crawl - cloudscraper ile"""
        logging.info(f"🌐 Crawl: {url[:60]}...")
        
        # Domain'e özel bekleme
        domain = self._extract_domain(url)
        if any(site in domain for site in ['trademo.com', 'volza.com', 'eximpedia.app']):
            wait_time = random.uniform(5, 8)  # Daha uzun bekleme
            logging.info(f"⏳ {domain} için {wait_time:.1f}s bekleme...")
            time.sleep(wait_time)
        
        # Önce cloudscraper ile dene
        page_result = self._try_cloudscraper_crawl(url, target_country)
        if page_result['status_code'] == 200:
            return page_result
        
        # Cloudscraper başarısızsa, normal requests ile dene
        page_result = self._try_page_crawl(url, target_country)
        if page_result['status_code'] == 200:
            return page_result
        
        # Her ikisi de başarısızsa snippet analizi
        logging.info(f"🔍 Snippet derinlemesine analiz: {url}")
        snippet_analysis = self.analyze_snippet_deep("", target_country, url)
        return {
            'country_found': snippet_analysis['country_found'], 
            'gtip_codes': snippet_analysis['gtip_codes'],
            'content_preview': 'Snippet analizi yapıldı',
            'status_code': 'SNIPPET_ANALYSIS'
        }
    
    def _try_cloudscraper_crawl(self, url, target_country):
        """Cloudscraper ile crawl dene"""
        try:
            logging.info(f"☁️ Cloudscraper ile deneme: {url}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Özel domain'ler için headers
            domain = self._extract_domain(url)
            if 'trademo.com' in domain:
                headers.update({
                    'Referer': 'https://www.trademo.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                })
            elif 'volza.com' in domain:
                headers.update({
                    'Referer': 'https://www.volza.com/',
                    'Sec-Fetch-Dest': 'document',
                })
            elif 'eximpedia.app' in domain:
                headers.update({
                    'Referer': 'https://www.eximpedia.app/',
                    'Sec-Fetch-Dest': 'document',
                })
            
            response = self.scraper.get(url, headers=headers, timeout=25)
            
            if response.status_code == 200:
                logging.info(f"✅ Cloudscraper başarılı: {url}")
                return self._parse_advanced_content(response.text, target_country, response.status_code)
            else:
                logging.warning(f"❌ Cloudscraper hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
        except Exception as e:
            logging.warning(f"❌ Cloudscraper hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'CLOUDSCRAPER_ERROR'}
    
    def _try_page_crawl(self, url, target_country):
        """Normal requests ile crawl dene"""
        try:
            logging.info(f"🌐 Normal requests ile deneme: {url}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Özel domain'ler için headers
            domain = self._extract_domain(url)
            if 'trademo.com' in domain:
                headers.update({
                    'Referer': 'https://www.trademo.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                })
            elif 'volza.com' in domain:
                headers.update({
                    'Referer': 'https://www.volza.com/',
                    'Sec-Fetch-Dest': 'document',
                })
            elif 'eximpedia.app' in domain:
                headers.update({
                    'Referer': 'https://www.eximpedia.app/',
                    'Sec-Fetch-Dest': 'document',
                })
            
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                logging.info(f"✅ Normal requests başarılı: {url}")
                return self._parse_advanced_content(response.text, target_country, response.status_code)
            elif response.status_code == 403:
                logging.warning(f"🔒 403 Forbidden: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 403}
            else:
                logging.warning(f"❌ Sayfa hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
        except requests.exceptions.Timeout:
            logging.warning(f"⏰ Timeout: {url}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'TIMEOUT'}
        except Exception as e:
            logging.error(f"❌ Sayfa crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_advanced_content(self, html, target_country, status_code):
        """Gelişmiş içerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            # Gelişmiş ülke kontrolü
            country_found = self._check_country_advanced(text_lower, target_country)
            
            # Gelişmiş GTIP kod çıkarma
            gtip_codes = self.extract_advanced_gtip_codes(text_content)
            
            logging.info(f"🔍 Sayfa analizi: Ülke={country_found}, GTIP={gtip_codes[:5]}")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': text_content[:300] + "..." if len(text_content) > 300 else text_content,
                'status_code': status_code
            }
        except Exception as e:
            logging.error(f"❌ Parse hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'PARSE_ERROR'}
    
    def _check_country_advanced(self, text_lower, target_country):
        """Gelişmiş ülke kontrolü"""
        country_variations = [
            target_country.lower(),
            target_country.upper(), 
            target_country.title(),
            'russia', 'rusya', 'rusian', 'rus'  # Rusya için özel varyasyonlar
        ]
        
        # Ticaret terimleri ile birlikte kontrol
        trade_terms = ['export', 'import', 'country', 'origin', 'destination', 'trade']
        
        for country_var in country_variations:
            if country_var in text_lower:
                # Ülke ismi geçiyorsa, ticaret terimleriyle yakınlık kontrolü
                for term in trade_terms:
                    if f"{term} {country_var}" in text_lower or f"{country_var} {term}" in text_lower:
                        logging.info(f"✅ Ülke bağlantısı bulundu: {term} {country_var}")
                        return True
                logging.info(f"✅ Ülke bağlantısı bulundu: {country_var}")
                return True
        
        return False
    
    def extract_advanced_gtip_codes(self, text):
        """Gelişmiş GTIP kod çıkarma"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',  # 8708.30 gibi
            r'\b\d{6}\b',  # 870830 gibi
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
            r'\bHarmonized\s?System\s?Code\s?:?\s?(\d{4,8})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Noktayı kaldır ve ilk 4 haneyi al
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    all_codes.add(code[:4])
                    logging.info(f"🔍 GTIP kodu bulundu: {code[:4]} (orijinal: {match})")
        
        return list(all_codes)
    
    def analyze_snippet_deep(self, snippet_text, target_country, url=""):
        """Snippet derinlemesine analizi - URL'den domain kontrolü"""
        domain = self._extract_domain(url)
        combined_text = f"{snippet_text} {domain}".lower()
        
        logging.info(f"🔍 Snippet analizi: {snippet_text[:100]}...")
        
        # Gelişmiş ülke kontrolü
        country_found = self._check_country_advanced(combined_text, target_country)
        
        # Gelişmiş GTIP çıkarma
        gtip_codes = self.extract_advanced_gtip_codes(snippet_text)
        
        # Domain'e özel pattern'ler
        if 'trademo.com' in domain:
            logging.info("🎯 Trademo.com özel analizi...")
            special_patterns = [
                (r'country of export.*russia', 'russia', 'country_found'),
                (r'export.*russia', 'russia', 'country_found'), 
                (r'hs code.*8708', '8708', 'gtip'),
                (r'8708.*hs code', '8708', 'gtip'),
                (r'870830', '8708', 'gtip'),
                (r'8708\.30', '8708', 'gtip'),
                (r'trademo', 'trademo', 'domain_trust'),  # Trademo domain güveni
            ]
            
            for pattern, value, pattern_type in special_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    if pattern_type == 'gtip' and value not in gtip_codes:
                        gtip_codes.append(value)
                        logging.info(f"🔍 Trademo özel pattern GTIP: {value}")
                    elif pattern_type == 'country_found' and not country_found:
                        country_found = True
                        logging.info(f"🔍 Trademo özel pattern ülke: {value}")
        
        logging.info(f"🔍 Snippet analizi sonucu: Ülke={country_found}, GTIP={gtip_codes}")
        
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

class EnhancedSearcher:
    def __init__(self, config):
        self.config = config
        self.crawler = AdvancedCrawler(config)
    
    def enhanced_search(self, query, max_results=3):
        """Gelişmiş arama - cloudscraper ile"""
        try:
            logging.info(f"🔍 DuckDuckGo: {query}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': '', 'kl': 'us-en'}
            
            # Uzun bekleme
            wait_time = random.uniform(3, 6)
            logging.info(f"⏳ Arama öncesi {wait_time:.1f}s bekleme...")
            time.sleep(wait_time)
            
            # Cloudscraper ile arama yap
            scraper = cloudscraper.create_scraper()
            response = scraper.post(url, data=data, headers=headers, timeout=25)
            
            if response.status_code == 200:
                results = self.parse_enhanced_results(response.text, max_results)
                logging.info(f"✅ {len(results)} sonuç bulundu")
                return results
            else:
                logging.warning(f"❌ DuckDuckGo hatası: {response.status_code}")
                return []
        except Exception as e:
            logging.error(f"❌ Arama hatası: {e}")
            return []
    
    def parse_enhanced_results(self, html, max_results):
        """Gelişmiş sonuç parse"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for div in soup.find_all('div', class_='result')[:max_results]:
            try:
                title_elem = div.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                
                if url and '//duckduckgo.com/l/' in url:
                    try:
                        time.sleep(2)
                        scraper = cloudscraper.create_scraper()
                        redirect_response = scraper.get(url, timeout=10, allow_redirects=True)
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
                    'domain': self._extract_domain(url)
                })
                
                logging.info(f"📄 Bulunan: {title[:60]}...")
                logging.info(f"🌐 Domain: {self._extract_domain(url)}")
                
            except Exception as e:
                logging.error(f"❌ Sonuç parse hatası: {e}")
                continue
        
        return results
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

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
        
        logging.info(f"🔍 EUR-Lex kontrolü: {checked_codes}")
        
        for gtip_code in checked_codes:
            if gtip_code in self.sanction_cache:
                if self.sanction_cache[gtip_code]:
                    sanctioned_codes.append(gtip_code)
                    logging.info(f"⛔ Önbellekten yaptırımlı: {gtip_code}")
                continue
                
            try:
                wait_time = random.uniform(2, 4)
                logging.info(f"⏳ EUR-Lex öncesi {wait_time:.1f}s bekleme...")
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
                        logging.info(f"⛔ Yaptırımlı kod: {gtip_code}")
                    else:
                        self.sanction_cache[gtip_code] = False
                        logging.info(f"✅ Kod temiz: {gtip_code}")
                else:
                    logging.warning(f"❌ EUR-Lex hatası: {response.status_code}")
                
            except Exception as e:
                logging.error(f"❌ EUR-Lex kontrol hatası: {e}")
                continue
        
        return sanctioned_codes

class EnhancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = EnhancedSearcher(config)
        self.crawler = AdvancedCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
    
    def enhanced_analyze(self, company, country):
        """Gelişmiş analiz - cloudscraper ile"""
        logging.info(f"🤖 GELİŞMİŞ ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business",
            f"{company} {country} HS code",
            f"{company} {country} trade"
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                logging.info(f"🔍 Sorgu {i}/4: {query}")
                
                # Sorgular arası uzun bekleme
                if i > 1:
                    wait_time = random.uniform(5, 10)
                    logging.info(f"⏳ Sorgular arası {wait_time:.1f}s bekleme...")
                    time.sleep(wait_time)
                
                search_results = self.searcher.enhanced_search(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    logging.warning(f"⚠️ Bu sorgu için sonuç bulunamadı: {query}")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    logging.info(f"📄 Sonuç {j} analiz ediliyor: {result['title'][:50]}...")
                    
                    # Sonuçlar arası uzun bekleme
                    if j > 1:
                        wait_time = random.uniform(3, 6)
                        logging.info(f"⏳ Sonuçlar arası {wait_time:.1f}s bekleme...")
                        time.sleep(wait_time)
                    
                    # Gelişmiş crawl (cloudscraper ile)
                    crawl_result = self.crawler.advanced_crawl(result['url'], country)
                    
                    # Eğer sayfaya erişilemediyse, snippet derinlemesine analiz
                    if crawl_result['status_code'] not in [200, 403, 'TIMEOUT']:
                        snippet_analysis = self.crawler.analyze_snippet_deep(result['full_text'], country, result['url'])
                        if snippet_analysis['country_found'] or snippet_analysis['gtip_codes']:
                            crawl_result['country_found'] = snippet_analysis['country_found']
                            crawl_result['gtip_codes'] = snippet_analysis['gtip_codes']
                            logging.info(f"🔍 Snippet analizi sonucu: Ülke={snippet_analysis['country_found']}, GTIP={snippet_analysis['gtip_codes']}")
                    
                    # EUR-Lex kontrolü
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        logging.info(f"🔍 EUR-Lex kontrolü yapılıyor...")
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    # Güven seviyesi hesapla
                    confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
                    
                    analysis = self.create_enhanced_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips, confidence
                    )
                    
                    all_results.append(analysis)
                
            except Exception as e:
                logging.error(f"❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # Domain güveni
        trusted_domains = ['trademo.com', 'eximpedia.app', 'volza.com', 'importyet.com', 'emis.com']
        if any(trusted in domain for trusted in trusted_domains):
            confidence += 30
            logging.info(f"📊 Domain güveni: +30% ({domain})")
        
        # GTIP kodları
        if crawl_result['gtip_codes']:
            confidence += 25
            logging.info(f"📊 GTIP güveni: +25% ({len(crawl_result['gtip_codes'])} kod)")
        
        # Ülke bağlantısı
        if crawl_result['country_found']:
            confidence += 25
            logging.info(f"📊 Ülke bağlantısı güveni: +25%")
        
        # Yaptırım tespiti
        if sanctioned_gtips:
            confidence += 20
            logging.info(f"📊 Yaptırım tespiti güveni: +20% ({len(sanctioned_gtips)} yaptırımlı kod)")
        
        final_confidence = min(confidence, 100)
        logging.info(f"📊 Toplam güven seviyesi: %{final_confidence}")
        
        return final_confidence
    
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
            'NEDENLER': ' | '.join(reasons) if reasons else 'Belirsiz'
        }

# Kalan fonksiyonlar aynı kalacak...
def create_detailed_excel_report(results, company, country):
    """Detaylı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        wb = Workbook()
        
        # 1. Sayfa: Analiz Sonuçları
        ws1 = wb.active
        ws1.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'GÜVEN_SEVİYESİ', 'NEDENLER',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET'
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
        
        # 2. Sayfa: Yapay Zeka Özeti
        ws2 = wb.create_sheet("AI Analiz Özeti")
        
        # Başlık
        ws2.merge_cells('A1:H1')
        title_cell = ws2.cell(row=1, column=1, value="YAPAY ZEKA TİCARET ANALİZ YORUMU")
        title_cell.font = Font(bold=True, size=16)
        
        # Şirket ve Ülke Bilgisi
        ws2.cell(row=3, column=1, value="ŞİRKET:")
        ws2.cell(row=3, column=2, value=company)
        ws2.cell(row=4, column=1, value="ÜLKE:")
        ws2.cell(row=4, column=2, value=country)
        ws2.cell(row=5, column=1, value="ANALİZ TARİHİ:")
        ws2.cell(row=5, column=2, value=datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        # Özet Bilgiler
        ws2.cell(row=7, column=1, value="TOPLAM SONUÇ:")
        ws2.cell(row=7, column=2, value=len(results))
        
        high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
        medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
        country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
        
        ws2.cell(row=8, column=1, value="YÜKSEK RİSK:")
        ws2.cell(row=8, column=2, value=high_risk_count)
        ws2.cell(row=9, column=1, value="ORTA RİSK:")
        ws2.cell(row=9, column=2, value=medium_risk_count)
        ws2.cell(row=10, column=1, value="ÜLKE BAĞLANTISI:")
        ws2.cell(row=10, column=2, value=country_connection_count)
        
        # Ortalama Güven Seviyesi
        avg_confidence = 0
        confidence_values = [int(r.get('GÜVEN_SEVİYESİ', '0%').strip('%')) for r in results if r.get('GÜVEN_SEVİYESİ')]
        if confidence_values:
            avg_confidence = sum(confidence_values) // len(confidence_values)
        
        ws2.cell(row=11, column=1, value="ORTALAMA GÜVEN:")
        ws2.cell(row=11, column=2, value=f"%{avg_confidence}")
        
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
        
        wb.save(filepath)
        logging.info(f"✅ Detaylı Excel raporu oluşturuldu: {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"❌ Excel rapor oluşturma hatası: {e}")
        return None

# Flask Route'ları
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        start_time = time.time()
        
        data = request.get_json()
        company = data.get('company', '').strip()
        country = data.get('country', '').strip()
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        logging.info(f"🚀 GELİŞMİŞ ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = EnhancedTradeAnalyzer(config)
        
        results = analyzer.enhanced_analyze(company, country)
        
        excel_filepath = create_detailed_excel_report(results, company, country)
        
        execution_time = time.time() - start_time
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
            "execution_time": f"{execution_time:.2f}s",
            "total_results": len(results),
            "analysis": results,
            "excel_download_url": f"/download-excel?company={company}&country={country}" if excel_filepath else None
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"❌ Analiz hatası: {e}")
        return jsonify({"error": f"Sunucu hatası: {str(e)}"}), 500

@app.route('/download-excel')
def download_excel():
    try:
        company = request.args.get('company', '')
        country = request.args.get('country', '')
        
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({"error": "Excel dosyası bulunamadı"}), 404
            
    except Exception as e:
        logging.error(f"❌ Excel indirme hatası: {e}")
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
