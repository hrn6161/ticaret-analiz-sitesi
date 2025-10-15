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

print("🚀 AKILLI FİRMA ANALİZ SİSTEMİ")

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
        self.MAX_RESULTS = 8
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def smart_crawl(self, url, target_country):
        """Akıllı crawl - sadece ticari siteler"""
        print(f"   🌐 Crawl: {url[:60]}...")
        
        # Önce domain kontrolü - sadece ticari siteler
        if not self._is_commercial_domain(url):
            print(f"   🔍 Ticari olmayan site atlandı: {url}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'NON_COMMERCIAL'}
        
        time.sleep(1)
        
        result = self._try_cloudscraper(url, target_country)
        if result['status_code'] == 200:
            return result
        
        result = self._try_requests(url, target_country)
        if result['status_code'] == 200:
            return result
        
        print(f"   🔍 Sayfa erişilemiyor, snippet analizi kullanılıyor...")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'BLOCKED'}
    
    def _is_commercial_domain(self, url):
        """Sadece ticari ve ticaret sitelerine izin ver"""
        commercial_domains = [
            'eximpedia', 'trademo', 'volza', 'exportgenius', 'comtrade',
            'alibaba', 'tradeindia', 'indiamart', 'go4worldbusiness',
            'kompass', 'globaltrade', 'worldtrade', 'tradekey',
            'companylist', 'exporters', 'suppliers', 'manufacturers',
            'business', 'trade', 'export', 'import', 'commerce',
            'customs', 'shipping', 'logistics', 'freight'
        ]
        
        spam_domains = [
            'donanımhaber', 'forum', 'blog', 'pdf', 'edu', 'academia',
            'wikipedia', 'social', 'facebook', 'twitter', 'instagram',
            'youtube', 'reddit', 'pinterest', 'tumblr'
        ]
        
        domain = url.lower()
        
        # Spam domain'leri engelle
        if any(spam in domain for spam in spam_domains):
            return False
        
        # Ticari domain'leri kabul et
        if any(commercial in domain for commercial in commercial_domains):
            return True
        
        return False
    
    def _try_cloudscraper(self, url, target_country):
        """Cloudscraper ile dene"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
        """İçerik analizi - geliştirilmiş"""
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
        """Ülke kontrolü - daha spesifik"""
        country_variations = {
            'russia': ['russia', 'rusya', 'russian', 'rus', 'rossiya', 'rf'],
            'china': ['china', 'çin', 'chinese'],
            'iran': ['iran', 'irani', 'persian']
        }
        
        if target_country.lower() in country_variations:
            variations = country_variations[target_country.lower()]
            for variation in variations:
                if variation in text_lower:
                    return True
        
        return False
    
    def extract_gtip_codes(self, text):
        """GTIP kod çıkarma - daha doğru"""
        # Sadece gerçek GTIP formatları
        patterns = [
            r'\b\d{4}\.\d{2}\b',  # 8708.29 gibi
            r'\bGTIP[: ]*(\d{4}\.?\d{0,4})\b',
            r'\bHS[: ]*CODE[: ]*(\d{4}\.?\d{0,4})\b',
            r'\bH\.S\. Code[: ]*(\d{4}\.?\d{0,4})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                # Sadece 4-8 haneli ve anlamlı GTIP'ler
                if len(code) >= 4 and len(code) <= 8:
                    # Yılları filtrele (2023, 2024, 2025 gibi)
                    if not self._is_year(code):
                        all_codes.add(code[:4])  # İlk 4 hane
        
        return list(all_codes)
    
    def _is_year(self, code):
        """Yıl olup olmadığını kontrol et"""
        if len(code) == 4:
            year = int(code)
            # 1900-2030 arası yılları filtrele
            if 1900 <= year <= 2030:
                return True
        return False

class QualitySearcher:
    """Kaliteli arama - sadece ticari sonuçlar"""
    
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        print("   🔍 KALİTELİ ARAMA MOTORU HAZIR!")
    
    def search_quality(self, query, max_results=8):
        """Sadece kaliteli, ticari sonuçları ara"""
        print(f"   🔍 Kaliteli arama: {query}")
        
        time.sleep(2)
        
        # DuckDuckGo Lite ile başla
        results = self._search_duckduckgo_lite(query, max_results)
        if results:
            print(f"   ✅ DuckDuckGo: {len(results)} kaliteli sonuç")
            return results
        
        print("   ❌ Kaliteli sonuç bulunamadı")
        return []
    
    def _search_duckduckgo_lite(self, query, max_results):
        """DuckDuckGo Lite - daha temiz sonuçlar"""
        try:
            url = "https://lite.duckduckgo.com/lite/"
            data = {
                'q': f"{query} site:eximpedia.app OR site:trademo.com OR site:volza.com OR site:exportgenius.in",
                'b': '',
            }
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            response = self.scraper.post(url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._parse_quality_results(response.text, max_results)
            else:
                print(f"   ❌ DuckDuckGo hatası {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ DuckDuckGo hatası: {e}")
            return []
    
    def _parse_quality_results(self, html, max_results):
        """Kaliteli sonuçları parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # DuckDuckGo Lite formatı
        rows = soup.find_all('tr')
        
        for i in range(0, len(rows)-1, 3):
            if len(results) >= max_results:
                break
                
            try:
                # Başlık satırı
                title_row = rows[i]
                link_elem = title_row.find('a', href=True)
                if not link_elem:
                    continue
                    
                title = link_elem.get_text(strip=True)
                url = link_elem.get('href')
                
                # URL kontrolü
                if not url or not self._is_quality_url(url):
                    continue
                
                # Snippet satırı
                snippet_row = rows[i+1] if i+1 < len(rows) else None
                snippet = ""
                if snippet_row:
                    snippet_elem = snippet_row.find('td')
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
                
                print(f"   📄 Kaliteli sonuç: {title[:50]}...")
                
            except Exception as e:
                continue
        
        return results
    
    def _is_quality_url(self, url):
        """Sadece kaliteli ticaret URL'lerini kabul et"""
        quality_domains = [
            'eximpedia.app', 'trademo.com', 'volza.com', 'exportgenius.in',
            'comtrade.un.org', 'alibaba.com', 'tradeindia.com'
        ]
        
        domain = self._extract_domain(url)
        return any(quality_domain in domain for quality_domain in quality_domains)
    
    def _extract_domain(self, url):
        """Domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class ExactQueryGenerator:
    """TAM FİRMA ADLI sorgu generator"""
    
    @staticmethod
    def generate_queries(company, country):
        """TAM FİRMA ADI ile 5 kaliteli sorgu"""
        
        queries = [
            # En spesifik sorgular
            f'"{company}" {country} export',
            f'"{company}" {country} import',
            f'"{company}" {country}',
            # Genel ticaret sorguları
            f'"{company}" trade',
            f'"{company}" customs'
        ]
        
        print(f"   🔍 {len(queries)} KALİTELİ sorgu oluşturuldu")
        return queries

class QuickEURLexChecker:
    def __init__(self, config):
        self.config = config
        self.sanction_cache = {}
    
    def quick_check_gtip(self, gtip_codes):
        """GTIP kontrolü - sadece gerçek GTIP'ler"""
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
                
                # Sadece Rusya için kontrol et
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'text': f'"{gtip_code}" Russia sanction',
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

class SmartTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = QualitySearcher(config)
        self.crawler = SmartCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
        self.query_generator = ExactQueryGenerator()
    
    def smart_analyze(self, company, country):
        """AKILLI ANALİZ - sadece kaliteli sonuçlar"""
        print(f"🤖 AKILLI ANALİZ: '{company}' ↔ {country}")
        
        search_queries = self.query_generator.generate_queries(company, country)
        
        all_results = []
        found_urls = set()
        country_connection_found = False
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"\n🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                if i > 1:
                    time.sleep(3)  # Kısa bekleme
                
                search_results = self.searcher.search_quality(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    print(f"   ⚠️ Kaliteli sonuç bulunamadı: {query}")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    if result['url'] in found_urls:
                        continue
                    
                    found_urls.add(result['url'])
                    
                    print(f"   📄 Kaliteli sonuç {j}: {result['title'][:50]}...")
                    
                    if j > 1:
                        time.sleep(1)
                    
                    # Snippet analizi
                    snippet_analysis = self._analyze_snippet(result['full_text'], country, result['url'])
                    
                    # Sayfa analizi
                    crawl_result = self.crawler.smart_crawl(result['url'], country)
                    
                    # Eğer sayfa ticari değilse atla
                    if crawl_result['status_code'] == 'NON_COMMERCIAL':
                        continue
                    
                    # Ülke bağlantısı kontrolü
                    if crawl_result['country_found']:
                        country_connection_found = True
                        print(f"   🚨 ÜLKE BAĞLANTISI TESPİT EDİLDİ: {company} ↔ {country}")
                    
                    # GTIP kontrolü
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
                    
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips, confidence, country_connection_found
                    )
                    
                    all_results.append(analysis)
                    
                    if len(all_results) >= 3:  # Sadece en iyi 3 sonuç
                        print("   🎯 3 kaliteli sonuç bulundu, analiz tamamlanıyor...")
                        return all_results
                
            except Exception as e:
                print(f"   ❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _analyze_snippet(self, snippet_text, target_country, url=""):
        """Snippet analizi"""
        domain = self._extract_domain(url)
        combined_text = f"{snippet_text} {domain}".lower()
        
        country_found = self._check_country_snippet(combined_text, target_country)
        gtip_codes = self._extract_gtip_snippet(snippet_text)
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes
        }
    
    def _check_country_snippet(self, text_lower, target_country):
        """Snippet ülke kontrolü"""
        country_variations = {
            'russia': ['russia', 'rusya', 'russian', 'rus'],
            'china': ['china', 'çin'],
            'iran': ['iran', 'irani']
        }
        
        if target_country.lower() in country_variations:
            variations = country_variations[target_country.lower()]
            for variation in variations:
                if variation in text_lower:
                    return True
        
        return False
    
    def _extract_gtip_snippet(self, text):
        """Snippet GTIP çıkarma"""
        patterns = [
            r'\b\d{4}\.\d{2}\b',
            r'\bGTIP[: ]*(\d{4}\.?\d{0,4})\b',
            r'\bHS[: ]*CODE[: ]*(\d{4}\.?\d{0,4})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4 and len(code) <= 8:
                    # Yılları filtrele
                    if not self._is_year(code):
                        all_codes.add(code[:4])
        
        return list(all_codes)
    
    def _is_year(self, code):
        """Yıl kontrolü"""
        if len(code) == 4:
            try:
                year = int(code)
                return 1900 <= year <= 2030
            except:
                pass
        return False
    
    def _extract_domain(self, url):
        """Domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi"""
        confidence = 0
        
        if crawl_result['country_found']:
            confidence += 50
        
        if crawl_result['gtip_codes']:
            confidence += 30
        
        if sanctioned_gtips:
            confidence += 20
        
        return min(confidence, 100)
    
    def create_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips, confidence, country_connection_found):
        """Analiz sonucu - basit ve net"""
        
        if country_connection_found:
            if sanctioned_gtips:
                status = "YÜKSEK_RİSK"
                explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yasaklı ürün ticareti yapıyor"
                ai_tavsiye = f"🔴 ACİL İNCELEME! Yasaklı GTIP: {', '.join(sanctioned_gtips)}"
                risk_level = "YÜKSEK"
            else:
                status = "RİSK_VAR"
                explanation = f"🟡 RİSK VAR: {company} şirketi {country} ile ticaret bağlantısı var"
                ai_tavsiye = "Ticaret bağlantısı doğrulandı. Detaylı inceleme önerilir."
                risk_level = "ORTA"
        else:
            status = "TEMİZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile bağlantısı bulunamadı"
            ai_tavsiye = "Risk bulunamadı"
            risk_level = "YOK"
        
        return {
            'ŞİRKET': company,
            'ÜLKE': country,
            'DURUM': status,
            'AI_AÇIKLAMA': explanation,
            'AI_TAVSIYE': ai_tavsiye,
            'YAPTIRIM_RISKI': risk_level,
            'TESPIT_EDILEN_GTIPLER': ', '.join(crawl_result['gtip_codes'][:3]),
            'YAPTIRIMLI_GTIPLER': ', '.join(sanctioned_gtips),
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
            'BAŞLIK': search_result['title'],
            'URL': search_result['url'],
            'ÖZET': search_result['snippet'],
            'GÜVEN_SEVİYESİ': f"%{confidence}",
            'KAYNAK_TİPİ': 'KALİTELİ'
        }

def create_excel_report(results, company, country):
    """Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
        
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
    print(f"📊 AKILLI ANALİZ SONUÇLARI: '{company}' ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Kaliteli analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    
    print(f"\n📈 ÖZET:")
    print(f"   • Toplam Kaliteli Sonuç: {total_results}")
    print(f"   • Ülke Bağlantısı: {country_connection_count}")
    print(f"   • YÜKSEK Yaptırım Riski: {high_risk_count}")
    print(f"   • ORTA Risk: {medium_risk_count}")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK RİSK UYARISI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YÜKSEK':
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
        print(f"   📍 Kaynak Tipi: {result.get('KAYNAK_TİPİ', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 AKILLI FİRMA ANALİZ SİSTEMİ")
    print("🎯 HEDEF: Sadece kaliteli, ticari sonuçlar")
    print("💡 AVANTAJ: Spam filtreleme, doğru GTIP tespiti")
    print("🔍 Arama: DuckDuckGo Lite + Ticari siteler\n")
    
    config = Config()
    analyzer = SmartTradeAnalyzer(config)
    
    company = input("Şirket adını girin (TAM İSİM): ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 AKILLI ANALİZ BAŞLATILIYOR: '{company}' ↔ {country}")
    print("⏳ Sadece kaliteli ticaret siteleri taranıyor...")
    print("   Spam ve alakasız sonuçlar otomatik filtreleniyor...\n")
    
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
        print("❌ Kaliteli analiz sonucu bulunamadı!")

if __name__ == "__main__":
    main()
