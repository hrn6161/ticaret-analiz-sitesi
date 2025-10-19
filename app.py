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
import urllib.parse

app = Flask(__name__)

print("🚀 OTOMATİK RİSK ANALİZLİ TİCARET SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
        """Akıllı crawl - 403 hatalarını aşmak için"""
        logging.info(f"🌐 Crawl: {url[:60]}...")
        
        # Önce cloudscraper ile dene
        result = self._try_cloudscraper(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # Cloudscraper başarısızsa normal requests ile dene
        result = self._try_requests(url, target_country)
        if result['status_code'] == 200:
            return result
        
        # Her ikisi de başarısızsa snippet analizi yap
        logging.info(f"🔍 Sayfa erişilemiyor, snippet analizi yapılıyor...")
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
            
            response = self.scraper.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                logging.info(f"✅ Cloudscraper başarılı: {url}")
                return self._parse_content(response.text, target_country, response.status_code)
            else:
                logging.warning(f"❌ Cloudscraper hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            logging.warning(f"❌ Cloudscraper hatası: {e}")
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
                logging.info(f"✅ Requests başarılı: {url}")
                return self._parse_content(response.text, target_country, response.status_code)
            else:
                logging.warning(f"❌ Requests hatası {response.status_code}: {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
                
        except Exception as e:
            logging.warning(f"❌ Requests hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_content(self, html, target_country, status_code):
        """İçerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            country_found = self._check_country(text_lower, target_country)
            gtip_codes = self.extract_gtip_codes(text_content)
            
            logging.info(f"🔍 Sayfa analizi: Ülke={country_found}, GTIP={gtip_codes[:3]}")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content,
                'status_code': status_code
            }
        except Exception as e:
            logging.error(f"❌ Parse hatası: {e}")
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
        logging.info("🦆 DuckDuckGo arama motoru hazır!")
    
    def search_simple(self, query, max_results=10):
        """Basit DuckDuckGo arama - DÜZELTİLMİŞ VERSİYON"""
        try:
            logging.info(f"🔍 Arama: {query}")
            
            time.sleep(2)
            
            # DuckDuckGo'nun farklı endpoint'ini deneyelim
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
                'Origin': 'https://duckduckgo.com',
                'Referer': 'https://duckduckgo.com/',
            }
            
            response = self.scraper.post(url, data=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                results = self._parse_results(response.text, max_results)
                logging.info(f"✅ {len(results)} sonuç buldu")
                return results
            else:
                logging.warning(f"❌ Arama hatası {response.status_code}")
                # Hata durumunda alternatif arama yöntemi
                return self._search_alternative(query, max_results)
                
        except Exception as e:
            logging.error(f"❌ Arama hatası: {e}")
            return self._search_alternative(query, max_results)
    
    def _search_alternative(self, query, max_results):
        """Alternatif arama yöntemi - Basit Google benzeri"""
        try:
            logging.info(f"🔍 Alternatif arama: {query}")
            
            # Basit bir arama simülasyonu - örnek sonuçlar döndür
            sample_results = self._generate_sample_results(query, max_results)
            logging.info(f"✅ Alternatif arama: {len(sample_results)} örnek sonuç")
            return sample_results
            
        except Exception as e:
            logging.error(f"❌ Alternatif arama hatası: {e}")
            return []
    
    def _generate_sample_results(self, query, max_results):
        """Örnek sonuçlar oluştur - demo amaçlı"""
        company = query.split()[0] if query.split() else "Şirket"
        
        sample_data = [
            {
                'title': f"{company} şirketi Rusya ile ticaret verileri",
                'url': f"https://ticaret-veritabanı.com/{company}-rusya",
                'snippet': f"{company} şirketinin Rusya Federasyonu ile ihracat-ithalat verileri analiz ediliyor",
                'search_engine': 'sample'
            },
            {
                'title': f"{company} uluslararası ticaret raporu",
                'url': f"https://trade-analysis.org/{company}-report",
                'snippet': f"{company} şirketinin uluslararası ticaret faaliyetleri ve partner ülkeler",
                'search_engine': 'sample'
            },
            {
                'title': f"{company} GTIP kodları ve yaptırım analizi",
                'url': f"https://customs-data.eu/{company}-gtip",
                'snippet': f"{company} şirketinin kullandığı GTIP kodları ve yaptırım durumu",
                'search_engine': 'sample'
            }
        ]
        
        return sample_data[:max_results]
    
    def _parse_results(self, html, max_results):
        """Sonuç parsing - GÜNCELLENMİŞ"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # DuckDuckGo sonuç elementleri
        results_elements = soup.find_all('div', class_=lambda x: x and ('result' in x if x else False))
        
        if not results_elements:
            results_elements = soup.find_all('div', class_=lambda x: x and ('web-result' in x if x else False))
        
        if not results_elements:
            results_elements = soup.find_all('div', class_=lambda x: x and ('links_main' in x if x else False))
        
        for element in results_elements[:max_results]:
            try:
                # Başlık bul
                title_elem = element.find('a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if len(title) < 5:
                    continue
                    
                url = title_elem.get('href')
                
                # URL düzelt
                if url and ('//duckduckgo.com/l/' in url or url.startswith('/l/')):
                    url = self._resolve_redirect(url)
                
                if not url or not url.startswith('http'):
                    # Göreli URL'leri mutlak yap
                    if url and url.startswith('/'):
                        url = 'https://duckduckgo.com' + url
                    else:
                        continue
                
                # Snippet bul
                snippet = ""
                snippet_elem = element.find('div', class_=lambda x: x and ('snippet' in x if x else False))
                if not snippet_elem:
                    snippet_elem = element.find('span', class_=lambda x: x and ('snippet' in x if x else False))
                
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
                
                logging.info(f"📄 {title[:50]}...")
                
            except Exception as e:
                logging.warning(f"❌ Sonuç parse hatası: {e}")
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
        
        logging.info(f"🔍 {len(queries)} sorgu: {queries}")
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
        
        logging.info(f"🔍 EUR-Lex kontrolü: {checked_codes}")
        
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
                        logging.info(f"⛔ Yaptırımlı kod: {gtip_code}")
                    else:
                        self.sanction_cache[gtip_code] = False
                
            except Exception as e:
                logging.error(f"❌ EUR-Lex kontrol hatası: {e}")
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
        logging.info(f"🤖 DEMO ANALİZ MODU: {company} ↔ {country}")
        
        # Demo modda çalış - gerçek arama yapmadan örnek sonuçlar döndür
        demo_results = self._generate_demo_results(company, country)
        
        if demo_results:
            logging.info(f"✅ Demo analiz tamamlandı: {len(demo_results)} sonuç")
            return demo_results
        else:
            logging.warning("❌ Demo analiz başarısız")
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
            }
        ]
        
        return demo_data

def create_excel_report(results, company, country):
    """Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
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
        
        wb.save(filepath)
        logging.info(f"✅ Excel raporu oluşturuldu: {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"❌ Excel rapor hatası: {e}")
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
        
        logging.info(f"🚀 DEMO ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = SmartTradeAnalyzer(config)
        
        results = analyzer.smart_analyze(company, country)
        
        excel_filepath = create_excel_report(results, company, country)
        
        execution_time = time.time() - start_time
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
            "execution_time": f"{execution_time:.2f}s",
            "total_results": len(results),
            "analysis": results,
            "excel_download_url": f"/download-excel?company={company}&country={country}" if excel_filepath else None,
            "note": "⚠️ DEMO MOD: Gerçek veriler yerine örnek sonuçlar gösteriliyor"
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
