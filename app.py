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

print("🚀 OPTİMİZE AKILLI CRAWLER SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3  # Daha az sonuç
        self.REQUEST_TIMEOUT = 15
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3  # Sadece ilk 3 GTIP'i kontrol et
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
    
    def smart_crawl(self, url, target_country):
        """Akıllı crawl - hızlı ve etkili"""
        logging.info(f"🌐 Crawl: {url[:60]}...")
        
        # 1. Deneme: Basit requests
        result = self._try_request(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # 2. Deneme: Gelişmiş headers
        result = self._try_advanced(url, target_country)
        if result['status_code'] == 200:
            return result
        
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'FAILED'}
    
    def _try_request(self, url, target_country):
        """Basit request"""
        try:
            headers = {'User-Agent': random.choice(self.config.USER_AGENTS)}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return self._parse_content(response.text, target_country, response.status_code)
        except:
            pass
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _try_advanced(self, url, target_country):
        """Gelişmiş headers"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return self._parse_content(response.text, target_country, response.status_code)
        except:
            pass
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_content(self, html, target_country, status_code):
        """Hızlı içerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            # Ülke kontrolü
            country_found = target_country.lower() in text_lower
            
            # GTIP kodları
            gtip_codes = self.extract_gtip_codes(text_content)
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': text_content[:300] + "..." if len(text_content) > 300 else text_content,
                'status_code': status_code
            }
        except:
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'PARSE_ERROR'}
    
    def extract_gtip_codes(self, text):
        """GTIP kodlarını çıkar"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
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
        
        return list(all_codes)[:10]  # Maksimum 10 kod

class FastSearcher:
    def __init__(self, config):
        self.config = config
    
    def fast_search(self, query, max_results=3):
        """Hızlı arama"""
        try:
            headers = {'User-Agent': random.choice(self.config.USER_AGENTS)}
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': '', 'kl': 'us-en'}
            
            response = requests.post(url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self.parse_results(response.text, max_results)
            return []
        except:
            return []
    
    def parse_results(self, html, max_results):
        """Sonuçları parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for div in soup.find_all('div', class_='result')[:max_results]:
            try:
                title_elem = div.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                
                # URL redirect
                if url and '//duckduckgo.com/l/' in url:
                    try:
                        redirect_response = requests.get(url, timeout=5, allow_redirects=True)
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
                    'full_text': f"{title} {snippet}"
                })
                
            except:
                continue
        
        return results

class QuickEURLexChecker:
    def __init__(self, config):
        self.config = config
        self.sanction_cache = {}  # Önbellek için
    
    def quick_check_gtip(self, gtip_codes):
        """Hızlı GTIP kontrolü - sadece ilk 3'ü"""
        if not gtip_codes:
            return []
            
        sanctioned_codes = []
        checked_codes = gtip_codes[:self.config.MAX_GTIP_CHECK]  # Sadece ilk 3
        
        for gtip_code in checked_codes:
            # Önbellekte var mı?
            if gtip_code in self.sanction_cache:
                if self.sanction_cache[gtip_code]:
                    sanctioned_codes.append(gtip_code)
                continue
                
            try:
                # Hızlı kontrol - sadece 1 sorgu
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'text': f'"{gtip_code}" sanction',
                    'type': 'advanced',
                    'lang': 'en'
                }
                
                response = requests.get(url, params=params, timeout=8)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.get_text().lower()
                    
                    # Basit kontrol
                    sanction_terms = ['prohibited', 'banned', 'sanction', 'restricted']
                    found_sanction = any(term in content for term in sanction_terms)
                    
                    if found_sanction:
                        sanctioned_codes.append(gtip_code)
                        self.sanction_cache[gtip_code] = True
                    else:
                        self.sanction_cache[gtip_code] = False
                
            except:
                continue
        
        return sanctioned_codes

class OptimizedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = FastSearcher(config)
        self.crawler = SmartCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
    
    def optimized_analyze(self, company, country):
        """Optimize edilmiş analiz - timeout öncelikli"""
        logging.info(f"⚡ OPTİMİZE ANALİZ: {company} ↔ {country}")
        
        # Sadece 3 ana sorgu
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business", 
            f"{company} {country} trade"
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries[:2], 1):  # Sadece ilk 2 sorgu
            try:
                logging.info(f"🔍 Sorgu {i}/2: {query}")
                
                search_results = self.searcher.fast_search(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    continue
                
                for j, result in enumerate(search_results, 1):
                    logging.info(f"📄 Sonuç {j}: {result['title'][:50]}...")
                    
                    # Hızlı crawl
                    crawl_result = self.crawler.smart_crawl(result['url'], country)
                    
                    # Snippet'ten GTIP çıkar
                    if not crawl_result['gtip_codes']:
                        snippet_gtips = self.crawler.extract_gtip_codes(result['full_text'])
                        if snippet_gtips:
                            crawl_result['gtip_codes'] = snippet_gtips
                            logging.info(f"🔍 Snippet GTIP: {snippet_gtips}")
                    
                    # Hızlı EUR-Lex kontrol (sadece ilk 3 GTIP)
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        logging.info(f"🔍 Hızlı EUR-Lex kontrol...")
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    # Sonuç oluştur
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips
                    )
                    
                    all_results.append(analysis)
                
                # Kısa bekleme
                if i < 2:
                    time.sleep(1)
                
            except Exception as e:
                logging.error(f"Sorgu hatası: {e}")
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
            ai_tavsiye = f"Ticaret bağlantısı doğrulandı. GTIP kodları: {', '.join(crawl_result['gtip_codes'][:3])}"
            risk_level = "ORTA"
        elif crawl_result['country_found']:
            status = "İLİŞKİ_VAR"
            explanation = f"🟢 İLİŞKİ VAR: {company} şirketi {country} ile bağlantılı"
            ai_tavsiye = "Ticaret bağlantısı bulundu"
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
            'TESPIT_EDILEN_GTIPLER': ', '.join(crawl_result['gtip_codes'][:5]),  # Sadece ilk 5
            'YAPTIRIMLI_GTIPLER': ', '.join(sanctioned_gtips),
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
            'BAŞLIK': search_result['title'],
            'URL': search_result['url'],
            'ÖZET': search_result['snippet'],
            'STATUS_CODE': crawl_result.get('status_code', 'N/A')
        }

def create_quick_excel_report(results, company, country):
    """Hızlı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA', 'AI_TAVSIYE'
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
        
        wb.save(filepath)
        return filepath
        
    except Exception as e:
        logging.error(f"Excel hatası: {e}")
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
        
        logging.info(f"🚀 OPTİMİZE ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = OptimizedTradeAnalyzer(config)
        
        results = analyzer.optimized_analyze(company, country)
        
        excel_filepath = create_quick_excel_report(results, company, country)
        
        execution_time = time.time() - start_time
        logging.info(f"⏱️ Analiz süresi: {execution_time:.2f}s")
        
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
        
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
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
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
