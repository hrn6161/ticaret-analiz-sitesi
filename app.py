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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

app = Flask(__name__)

print("🚀 SELENIUM İLE GELİŞMİŞ CRAWLER SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3
        self.REQUEST_TIMEOUT = 30
        self.SELENIUM_TIMEOUT = 45
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class SeleniumCrawler:
    def __init__(self, config):
        self.config = config
        self.driver = None
    
    def init_driver(self):
        """Selenium driver'ı başlat"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Render'da Chrome path'ini belirt
            chrome_options.binary_location = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Selenium driver başlatıldı")
            return True
        except Exception as e:
            logging.error(f"❌ Selenium driver başlatma hatası: {e}")
            return False
    
    def crawl_with_selenium(self, url, target_country):
        """Selenium ile sayfayı crawl et"""
        if not self.driver and not self.init_driver():
            return {'country_found': False, 'gtip_codes': [], 'content_preview': ''}
        
        try:
            logging.info(f"🌐 Selenium ile sayfa açılıyor: {url}")
            
            # Sayfayı aç
            self.driver.get(url)
            
            # Sayfanın yüklenmesini bekle
            WebDriverWait(self.driver, self.config.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Rastgele scroll ve bekleme (insan benzeri davranış)
            self._human_like_behavior()
            
            # Sayfa içeriğini al
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Script ve style tag'lerini temizle
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Tüm metni al
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_content = ' '.join(chunk for chunk in chunks if chunk)
            
            text_lower = cleaned_content.lower()
            
            # Ülke ismini ara
            country_found = target_country.lower() in text_lower
            
            # GTIP/HS kodlarını ara
            gtip_codes = self.extract_gtip_codes(cleaned_content)
            
            content_preview = cleaned_content[:400] + "..." if len(cleaned_content) > 400 else cleaned_content
            
            logging.info(f"🔍 Selenium analizi: Ülke bulundu={country_found}, GTIP kodları={gtip_codes}")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': content_preview,
                'status_code': 200
            }
            
        except TimeoutException:
            logging.error(f"❌ Selenium timeout: {url}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'TIMEOUT'}
        except Exception as e:
            logging.error(f"❌ Selenium hatası {url}: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _human_like_behavior(self):
        """İnsan benzeri davranış simülasyonu"""
        try:
            # Rastgele scroll
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            random_scroll = random.randint(100, min(800, scroll_height))
            self.driver.execute_script(f"window.scrollTo(0, {random_scroll});")
            
            # Rastgele bekleme
            time.sleep(random.uniform(2, 4))
            
            # Tekrar scroll
            random_scroll_2 = random.randint(200, min(1200, scroll_height))
            self.driver.execute_script(f"window.scrollTo(0, {random_scroll_2});")
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logging.warning(f"Scroll hatası: {e}")
    
    def extract_gtip_codes(self, text):
        """Metinden GTIP/HS kodlarını çıkar"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bHS\s?:?\s?(\d{4,8})\b',
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
                    main_code = code[:4]
                    if main_code.isdigit():
                        all_codes.add(main_code)
        
        return list(all_codes)
    
    def close_driver(self):
        """Driver'ı kapat"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

class DuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
    
    def search_duckduckgo(self, query, max_results=3):
        """DuckDuckGo'da arama yap"""
        try:
            logging.info(f"🔍 DuckDuckGo'da aranıyor: {query}")
            
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
                logging.warning(f"DuckDuckGo arama hatası: {response.status_code}")
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
                    'snippet': snippet
                })
                
                logging.info(f"📄 Bulunan sonuç: {title[:60]}...")
                
            except Exception as e:
                logging.error(f"Sonuç parse hatası: {e}")
                continue
        
        logging.info(f"✅ DuckDuckGo'dan {len(results)} sonuç bulundu")
        return results

class EURLexChecker:
    def __init__(self, config):
        self.config = config
    
    def check_gtip_in_eur_lex(self, gtip_codes):
        """GTIP kodlarını EUR-Lex'te kontrol et"""
        sanctioned_codes = []
        
        for gtip_code in gtip_codes:
            try:
                logging.info(f"🔍 EUR-Lex'te kontrol ediliyor: GTIP {gtip_code}")
                
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
                    ]
                    found_sanction = any(term in content for term in sanction_terms)
                    
                    if found_sanction:
                        sanctioned_codes.append(gtip_code)
                        logging.warning(f"⛔ Yaptırımlı kod bulundu: {gtip_code}")
                    else:
                        logging.info(f"✅ Kod temiz: {gtip_code}")
                else:
                    logging.warning(f"EUR-Lex erişim hatası: {response.status_code}")
                
            except Exception as e:
                logging.error(f"EUR-Lex kontrol hatası GTIP {gtip_code}: {e}")
                continue
        
        return sanctioned_codes

class AdvancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = DuckDuckGoSearcher(config)
        self.crawler = SeleniumCrawler(config)
        self.eur_lex_checker = EURLexChecker(config)
    
    def analyze_company_country(self, company, country):
        """Şirket-ülke analizi yap"""
        logging.info(f"🤖 SELENIUM ANALİZİ BAŞLATILIYOR: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business",
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                logging.info(f"🔍 Sorgu {i}/{len(search_queries)}: {query}")
                
                search_results = self.searcher.search_duckduckgo(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    logging.warning(f"❌ Bu sorgu için sonuç bulunamadı: {query}")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    logging.info(f"📄 Sonuç {j} analiz ediliyor: {result['title'][:50]}...")
                    
                    # Selenium ile crawl et
                    crawl_result = self.crawler.crawl_with_selenium(result['url'], country)
                    
                    # EUR-Lex kontrolü
                    sanctioned_gtips = []
                    if crawl_result['country_found'] and crawl_result['gtip_codes']:
                        logging.info(f"🔍 EUR-Lex kontrolü yapılıyor...")
                        sanctioned_gtips = self.eur_lex_checker.check_gtip_in_eur_lex(crawl_result['gtip_codes'])
                    
                    # Analiz sonucu oluştur
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips
                    )
                    
                    all_results.append(analysis)
                
                # Sorgular arasında bekleme
                if i < len(search_queries):
                    delay = random.uniform(3, 6)
                    logging.info(f"⏳ {delay:.1f} saniye bekleniyor...")
                    time.sleep(delay)
                
            except Exception as e:
                logging.error(f"❌ Sorgu hatası '{query}': {e}")
                continue
        
        # Driver'ı temizle
        self.crawler.close_driver()
        
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
            'CRAWLER_TIPI': 'SELENIUM'
        }

def create_excel_report(results, company, country):
    """Excel raporu oluştur"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_selenium_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Selenium Analiz Sonuçları"
        
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
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON verisi bekleniyor"}), 400
        
        company = data.get('company', '').strip()
        country = data.get('country', '').strip()
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        logging.info(f"🚀 SELENIUM ANALİZİ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = AdvancedTradeAnalyzer(config)
        
        results = analyzer.analyze_company_country(company, country)
        
        excel_filepath = create_excel_report(results, company, country)
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
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
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        filename = f"{company.replace(' ', '_')}_{country}_selenium_analiz.xlsx"
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
