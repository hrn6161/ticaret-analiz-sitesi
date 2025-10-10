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
import concurrent.futures
from threading import Thread
import urllib.parse

app = Flask(__name__)

print("🚀 GELİŞMİŞ AKILLI CRAWLER SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 5  # Daha fazla sonuç
        self.REQUEST_TIMEOUT = 20
        self.RETRY_ATTEMPTS = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        self.SEARCH_ENGINES = [
            "duckduckgo",
            "google"  # Google arama desteği
        ]

class AdvancedCrawler:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
    
    def advanced_crawl(self, url, target_country):
        """Gelişmiş crawl - çoklu teknikler"""
        logging.info(f"🌐 Gelişmiş crawl: {url}")
        
        # 1. Deneme: Basit requests
        result = self._try_basic_request(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # 2. Deneme: Gelişmiş headers
        result = self._try_advanced_headers(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # 3. Deneme: Session ile tekrar deneme
        result = self._try_with_session(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # 4. Deneme: Farklı User-Agent
        result = self._try_different_agent(url, target_country)
        if result['status_code'] == 200:
            return result
        
        logging.warning(f"⚠️  Tüm yöntemler başarısız: {url}")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ALL_FAILED'}
    
    def _try_basic_request(self, url, target_country):
        """Basit request dene"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return self._parse_advanced_content(response.text, target_country, response.status_code)
        except:
            pass
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'BASIC_FAILED'}
    
    def _try_advanced_headers(self, url, target_country):
        """Gelişmiş headers ile dene"""
        try:
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
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return self._parse_advanced_content(response.text, target_country, response.status_code)
        except:
            pass
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ADVANCED_FAILED'}
    
    def _try_with_session(self, url, target_country):
        """Session ile dene"""
        try:
            self.session.headers.update({
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            })
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return self._parse_advanced_content(response.text, target_country, response.status_code)
        except:
            pass
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'SESSION_FAILED'}
    
    def _try_different_agent(self, url, target_country):
        """Farklı User-Agent ile dene"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return self._parse_advanced_content(response.text, target_country, response.status_code)
        except:
            pass
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'AGENT_FAILED'}
    
    def _parse_advanced_content(self, html, target_country, status_code):
        """Gelişmiş içerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Meta description'ı al
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_content = meta_desc.get('content', '') if meta_desc else ''
            
            # Title'ı al
            title = soup.find('title')
            title_content = title.get_text() if title else ''
            
            # Tüm metni al
            text_content = soup.get_text()
            combined_content = f"{title_content} {meta_content} {text_content}"
            
            # Temizleme
            lines = (line.strip() for line in combined_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_content = ' '.join(chunk for chunk in chunks if chunk)
            
            text_lower = cleaned_content.lower()
            
            # Ülke ismini ara (farklı varyasyonlarla)
            country_variations = [
                target_country.lower(),
                target_country.upper(),
                target_country.title()
            ]
            country_found = any(variation in text_lower for variation in country_variations)
            
            # GTIP/HS kodlarını ara
            gtip_codes = self.extract_advanced_gtip_codes(cleaned_content)
            
            content_preview = cleaned_content[:500] + "..." if len(cleaned_content) > 500 else cleaned_content
            
            logging.info(f"🔍 Gelişmiş analiz: Ülke={country_found}, GTIP={gtip_codes}")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': content_preview,
                'status_code': status_code
            }
        except Exception as e:
            logging.error(f"Parse hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'PARSE_ERROR'}
    
    def extract_advanced_gtip_codes(self, text):
        """Gelişmiş GTIP kod çıkarma"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bHS\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
            r'\bHarmonized System\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bCustoms\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bTariff\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bProduct\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bItem\s?Code\s?:?\s?(\d{4,8})\b',
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
        
        # 4-8 haneli sayıları kontrol et (GTIP aralığında mı)
        number_pattern = r'\b\d{4,8}\b'
        numbers = re.findall(number_pattern, text)
        
        for num in numbers:
            if num.isdigit():
                num_int = int(num[:4])  # İlk 4 haneye bak
                # Geniş GTIP aralıkları
                gtip_ranges = [
                    (8400, 8600), (8700, 8900), (9000, 9300), 
                    (2800, 2900), (8470, 8480), (8500, 8520),
                    (8540, 8550), (9301, 9307), (4016, 4016),
                    (8708, 8708), (8542, 8542), (8471, 8471)
                ]
                for start, end in gtip_ranges:
                    if start <= num_int <= end:
                        all_codes.add(str(num_int))
                        break
        
        return list(all_codes)

class MultiSearcher:
    def __init__(self, config):
        self.config = config
    
    def comprehensive_search(self, query, max_results=5):
        """Kapsamlı arama - çoklu sorgular"""
        all_results = []
        
        # DuckDuckGo arama
        ddg_results = self.search_duckduckgo(query, max_results)
        all_results.extend(ddg_results)
        
        # Farklı sorgu varyasyonları
        query_variations = self.generate_query_variations(query)
        for variation in query_variations[:2]:  # İlk 2 varyasyon
            try:
                variation_results = self.search_duckduckgo(variation, max_results//2)
                all_results.extend(variation_results)
                time.sleep(1)  # Rate limiting
            except:
                pass
        
        # Benzersiz sonuçlar
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        logging.info(f"✅ Kapsamlı arama: {len(unique_results)} benzersiz sonuç")
        return unique_results[:max_results]
    
    def generate_query_variations(self, base_query):
        """Sorgu varyasyonları oluştur"""
        variations = [
            f"{base_query}",
            f"{base_query} company",
            f"{base_query} trade",
            f"{base_query} export import",
            f"{base_query} business relations",
            f"{base_query} trading partner",
            f"{base_query} commercial",
            f'"{base_query}"',
        ]
        return variations
    
    def search_duckduckgo(self, query, max_results=5):
        """DuckDuckGo'da arama"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            url = "https://html.duckduckgo.com/html/"
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                return self.parse_duckduckgo_results(response.text, max_results)
            else:
                logging.warning(f"DuckDuckGo hatası: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"DuckDuckGo arama hatası: {e}")
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
                
                # URL redirect
                if url and '//duckduckgo.com/l/' in url:
                    try:
                        redirect_response = requests.get(url, timeout=8, allow_redirects=True)
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
                    'search_engine': 'duckduckgo'
                })
                
            except Exception as e:
                logging.error(f"Sonuç parse hatası: {e}")
                continue
        
        return results

class EURLexChecker:
    def __init__(self, config):
        self.config = config
    
    def comprehensive_check_gtip(self, gtip_codes):
        """Kapsamlı GTIP kontrolü"""
        if not gtip_codes:
            return []
            
        sanctioned_codes = []
        
        for gtip_code in gtip_codes:
            try:
                logging.info(f"🔍 EUR-Lex kontrolü: GTIP {gtip_code}")
                
                time.sleep(random.uniform(1, 2))
                
                # Farklı sorgular deneyelim
                search_terms = [
                    f'"{gtip_code}" prohibited banned sanction',
                    f'"{gtip_code}" restricted embargo',
                    f'"{gtip_code}" not allowed export',
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
                        
                        sanction_terms = [
                            'prohibited', 'banned', 'sanction', 'restricted', 
                            'embargo', 'forbidden', 'prohibition', 'ban',
                            'not allowed', 'not permitted', 'restriction'
                        ]
                        found_sanction = any(term in content for term in sanction_terms)
                        
                        if found_sanction:
                            sanctioned_codes.append(gtip_code)
                            logging.warning(f"⛔ Yaptırımlı kod bulundu: {gtip_code}")
                            break  # Bir kere bulduysa diğerlerini kontrol etme
                        else:
                            logging.info(f"✅ Kod temiz: {gtip_code}")
                            break
                    else:
                        logging.warning(f"EUR-Lex erişim hatası: {response.status_code}")
                
            except Exception as e:
                logging.error(f"EUR-Lex kontrol hatası GTIP {gtip_code}: {e}")
                continue
        
        return sanctioned_codes

class ComprehensiveTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = MultiSearcher(config)
        self.crawler = AdvancedCrawler(config)
        self.eur_lex_checker = EURLexChecker(config)
    
    def comprehensive_analyze(self, company, country):
        """Kapsamlı analiz"""
        logging.info(f"🤖 KAPSAMLI ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
        
        # Çoklu arama sorguları
        search_queries = self.generate_search_queries(company, country)
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                logging.info(f"🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                search_results = self.searcher.comprehensive_search(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    logging.warning(f"❌ Bu sorgu için sonuç bulunamadı: {query}")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    logging.info(f"📄 Sonuç {j} analiz ediliyor: {result['title'][:50]}...")
                    
                    # Gelişmiş crawl
                    crawl_result = self.crawler.advanced_crawl(result['url'], country)
                    
                    # Snippet'ten GTIP çıkar
                    if not crawl_result['gtip_codes']:
                        snippet_gtips = self.crawler.extract_advanced_gtip_codes(result['full_text'])
                        if snippet_gtips:
                            crawl_result['gtip_codes'] = snippet_gtips
                            logging.info(f"🔍 Snippet'ten GTIP çıkarıldı: {snippet_gtips}")
                    
                    # EUR-Lex kontrolü
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        logging.info(f"🔍 EUR-Lex kontrolü yapılıyor...")
                        sanctioned_gtips = self.eur_lex_checker.comprehensive_check_gtip(crawl_result['gtip_codes'])
                    
                    # Analiz sonucu oluştur
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips
                    )
                    
                    all_results.append(analysis)
                
                # Sorgular arasında bekleme
                if i < len(search_queries):
                    delay = random.uniform(2, 4)
                    logging.info(f"⏳ {delay:.1f} saniye bekleniyor...")
                    time.sleep(delay)
                
            except Exception as e:
                logging.error(f"❌ Sorgu hatası '{query}': {e}")
                continue
        
        return all_results
    
    def generate_search_queries(self, company, country):
        """Arama sorguları oluştur"""
        queries = [
            f"{company} {country} export",
            f"{company} {country} import",
            f"{company} {country} trade",
            f"{company} {country} business",
            f"{company} {country} trading partner",
            f"{company} {country} commercial relations",
            f"{company} {country} distributor",
            f"{company} {country} supplier",
            f'"{company}" "{country}"',
            f"{company} {country} HS code",
            f"{company} {country} GTIP",
        ]
        return queries
    
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
            'CRAWLER_TIPI': 'GELİŞMİŞ_CRAWLER',
            'ARAMA_MOTORU': search_result.get('search_engine', 'duckduckgo')
        }

def create_comprehensive_excel_report(results, company, country):
    """Kapsamlı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_kapsamli_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Kapsamlı Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA',
            'AI_TAVSIYE', 'BAŞLIK', 'URL', 'CRAWLER_TIPI', 'ARAMA_MOTORU'
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
            ws.cell(row=row, column=13, value=str(result.get('ARAMA_MOTORU', '')))
        
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
        
        wb.save(filepath)
        logging.info(f"✅ Excel raporu oluşturuldu: {filepath}")
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
        
        logging.info(f"🚀 KAPSAMLI ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = ComprehensiveTradeAnalyzer(config)
        
        results = analyzer.comprehensive_analyze(company, country)
        
        excel_filepath = create_comprehensive_excel_report(results, company, country)
        
        execution_time = time.time() - start_time
        logging.info(f"⏱️ Toplam analiz süresi: {execution_time:.2f}s")
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
            "execution_time": f"{execution_time:.2f}s",
            "total_results": len(results),
            "total_queries": 11,  # 11 farklı sorgu
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
        
        filename = f"{company.replace(' ', '_')}_{country}_kapsamli_analiz.xlsx"
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
