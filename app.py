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

app = Flask(__name__)

print("🚀 DUCKDUCKGO İLE GERÇEK ARAMA SİSTEMİ BAŞLATILIYOR...")

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
        self.DELAY_BETWEEN_REQUESTS = 2.0
        self.DELAY_BETWEEN_SEARCHES = 3.0
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class DuckDuckGoSearcher:
    def __init__(self, config):
        self.config = config
    
    def search_duckduckgo(self, query, max_results=3):
        """DuckDuckGo'da gerçek arama yap"""
        try:
            logging.info(f"🔍 DuckDuckGo'da aranıyor: {query}")
            
            # Tırnak işaretlerini kaldır
            query = query.replace('"', '')
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
            }
            
            # DuckDuckGo HTML arama URL'si
            url = "https://html.duckduckgo.com/html/"
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            response = requests.post(
                url, 
                data=data, 
                headers=headers, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            
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
        
        # DuckDuckGo search result div'leri
        result_divs = soup.find_all('div', class_='result')
        
        for div in result_divs[:max_results]:
            try:
                # Başlık
                title_elem = div.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # URL
                url = title_elem.get('href')
                if url and '//duckduckgo.com/l/' in url:
                    # DuckDuckGo redirect link'ini çöz
                    try:
                        redirect_response = requests.get(url, timeout=10, allow_redirects=True)
                        url = redirect_response.url
                    except:
                        # Redirect çözülemezse orijinal URL'yi kullan
                        pass
                
                # Özet
                snippet_elem = div.find('a', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # URL'yi temizle
                if url and url.startswith('//'):
                    url = 'https:' + url
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
                
                logging.info(f"📄 Bulunan sonuç: {title[:50]}...")
                
            except Exception as e:
                logging.error(f"Sonuç parse hatası: {e}")
                continue
        
        logging.info(f"DuckDuckGo'dan {len(results)} sonuç bulundu")
        return results

class ContentCrawler:
    def __init__(self, config):
        self.config = config
    
    def crawl_page_content(self, url, target_country):
        """Sayfa içeriğini crawl et ve ülke bağlantısını ara"""
        try:
            if not url or not url.startswith('http'):
                return {'country_found': False, 'gtip_codes': [], 'content_preview': ''}
                
            logging.info(f"🌐 Sayfa crawl ediliyor: {url}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Script ve style tag'lerini temizle
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text_content = soup.get_text()
                text_lower = text_content.lower()
                
                # Ülke ismini ara (case insensitive)
                country_found = target_country.lower() in text_lower
                
                # GTIP/HS kodlarını ara
                gtip_codes = self.extract_gtip_codes(text_content)
                
                content_preview = text_content[:300] + "..." if len(text_content) > 300 else text_content
                content_preview = ' '.join(content_preview.split())  # Fazla boşlukları temizle
                
                logging.info(f"🔍 Sayfa analizi: Ülke bulundu={country_found}, GTIP kodları={gtip_codes}")
                
                return {
                    'country_found': country_found,
                    'gtip_codes': gtip_codes,
                    'content_preview': content_preview
                }
            else:
                logging.warning(f"Sayfa crawl hatası: {response.status_code} - {url}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': ''}
                
        except Exception as e:
            logging.error(f"Crawl hatası {url}: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': ''}
    
    def extract_gtip_codes(self, text):
        """Metinden GTIP/HS kodlarını çıkar"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bHS\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
            r'\bHarmonized System\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bCustoms\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bTariff\s?Code\s?:?\s?(\d{4,8})\b',
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
        
        # 4 haneli sayıları kontrol et (GTIP aralığında mı)
        number_pattern = r'\b\d{4}\b'
        numbers = re.findall(number_pattern, text)
        
        for num in numbers:
            if num.isdigit():
                num_int = int(num)
                # GTIP aralıkları
                if ((8400 <= num_int <= 8600) or (8700 <= num_int <= 8900) or 
                    (9000 <= num_int <= 9300) or (2800 <= num_int <= 2900) or
                    (8470 <= num_int <= 8480) or (8500 <= num_int <= 8520) or
                    (8540 <= num_int <= 8550) or (9301 <= num_int <= 9307)):
                    all_codes.add(num)
        
        return list(all_codes)

class EURLexChecker:
    def __init__(self, config):
        self.config = config
    
    def check_gtip_in_eur_lex(self, gtip_codes):
        """GTIP kodlarını EUR-Lex'te kontrol et"""
        sanctioned_codes = []
        
        for gtip_code in gtip_codes:
            try:
                logging.info(f"🔍 EUR-Lex'te kontrol ediliyor: GTIP {gtip_code}")
                
                # EUR-Lex arama URL'si
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'qid': int(time.time()),
                    'text': f'"{gtip_code}" prohibited banned sanction restricted',
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
                    
                    # Yaptırım terimlerini ara
                    sanction_terms = [
                        'prohibited', 'banned', 'sanction', 'restricted', 
                        'embargo', 'forbidden', 'prohibition', 'ban'
                    ]
                    found_sanction = any(term in content for term in sanction_terms)
                    
                    if found_sanction:
                        sanctioned_codes.append(gtip_code)
                        logging.warning(f"⛔ Yaptırımlı kod bulundu: {gtip_code}")
                    else:
                        logging.info(f"✅ Kod temiz: {gtip_code}")
                else:
                    logging.warning(f"EUR-Lex erişim hatası: {response.status_code}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logging.error(f"EUR-Lex kontrol hatası GTIP {gtip_code}: {e}")
                continue
        
        return sanctioned_codes

class AdvancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = DuckDuckGoSearcher(config)
        self.crawler = ContentCrawler(config)
        self.eur_lex_checker = EURLexChecker(config)
    
    def analyze_company_country(self, company, country):
        """Şirket-ülke analizi yap"""
        logging.info(f"🤖 GERÇEK ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business",
            f"{company} {country} trade relations",
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                logging.info(f"🔍 Sorgu çalıştırılıyor: {query}")
                
                # DuckDuckGo'da ara
                search_results = self.searcher.search_duckduckgo(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    logging.warning(f"❌ Bu sorgu için sonuç bulunamadı: {query}")
                    continue
                
                for result in search_results:
                    logging.info(f"📄 Sayfa analiz ediliyor: {result['title'][:50]}...")
                    
                    # Sayfayı crawl et
                    crawl_result = self.crawler.crawl_page_content(result['url'], country)
                    
                    # Eğer ülke bağlantısı bulunduysa ve GTIP kodları varsa, EUR-Lex kontrolü yap
                    sanctioned_gtips = []
                    if crawl_result['country_found'] and crawl_result['gtip_codes']:
                        logging.info(f"🔍 EUR-Lex kontrolü yapılıyor: {crawl_result['gtip_codes']}")
                        sanctioned_gtips = self.eur_lex_checker.check_gtip_in_eur_lex(crawl_result['gtip_codes'])
                    
                    # Analiz sonucu oluştur
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips
                    )
                    
                    all_results.append(analysis)
                    
                    # Kısa bekleme
                    time.sleep(1)
                
                # Sorgular arasında bekleme
                time.sleep(self.config.DELAY_BETWEEN_SEARCHES)
                
            except Exception as e:
                logging.error(f"Sorgu hatası '{query}': {e}")
                continue
        
        return all_results
    
    def create_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips):
        """Analiz sonucu oluştur"""
        
        # Risk değerlendirmesi
        if sanctioned_gtips:
            status = "YAPTIRIMLI_YÜKSEK_RISK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
            ai_tavsiye = f"⛔ ACİL DURUM! Bu ürünlerin {country.upper()} ihracı YASAKTIR: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif crawl_result['country_found'] and crawl_result['gtip_codes']:
            status = "RISK_VAR"
            explanation = f"🟡 RİSK VAR: {company} şirketi {country} ile ticaret bağlantısı bulundu"
            ai_tavsiye = f"Ticaret bağlantısı doğrulandı. GTIP kodları kontrol edildi: {', '.join(crawl_result['gtip_codes'])}"
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
            'ARAMA_MOTORU': 'DuckDuckGo'
        }

def create_excel_report(results, company, country):
    """Excel raporu oluştur"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_gercek_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "DuckDuckGo Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA',
            'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET', 'ARAMA_MOTORU'
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
            ws.cell(row=row, column=12, value=str(result.get('ÖZET', '')))
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
        logging.info(f"Excel raporu oluşturuldu: {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"Excel rapor oluşturma hatası: {e}")
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
        
        logging.info(f"🚀 GERÇEK DUCKDUCKGO ANALİZİ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = AdvancedTradeAnalyzer(config)
        
        # Gerçek analiz yap
        results = analyzer.analyze_company_country(company, country)
        
        # Excel raporu oluştur
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
        logging.error(f"Analiz hatası: {e}")
        return jsonify({"error": f"Sunucu hatası: {str(e)}"}), 500

@app.route('/download-excel')
def download_excel():
    try:
        company = request.args.get('company', '')
        country = request.args.get('country', '')
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        filename = f"{company.replace(' ', '_')}_{country}_gercek_analiz.xlsx"
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
        logging.error(f"Excel indirme hatası: {e}")
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
