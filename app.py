from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
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
from urllib.parse import urlparse, quote
import concurrent.futures

app = Flask(__name__)
# CORS'u tüm domain'ler için etkinleştir
CORS(app)

print("🚀 GÜNCELLENMİŞ TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AdvancedConfig:
    def __init__(self):
        self.MAX_RESULTS = 5
        self.REQUEST_TIMEOUT = 30
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        self.TRADE_SITES = ["trademo.com", "eximpedia.app", "volza.com"]

class SmartSearchEngine:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def quick_search(self, company, country):
        """Hızlı ve etkili arama"""
        print(f"🔍 HIZLI ARAMA: {company} ↔ {country}")
        
        all_results = []
        
        # 1. Ticaret sitelerinde hızlı arama
        trade_results = self._quick_trade_search(company, country)
        all_results.extend(trade_results)
        
        # 2. Basit Google araması
        google_results = self._simple_google_search(company, country)
        all_results.extend(google_results)
        
        print(f"   📊 {len(all_results)} sonuç bulundu")
        return all_results
    
    def _quick_trade_search(self, company, country):
        """Ticaret sitelerinde hızlı arama"""
        results = []
        
        # Trademo hızlı kontrol
        try:
            trademo_url = f"https://www.trademo.com/search/companies?q={quote(company)}"
            print(f"   🔎 Trademo kontrol...")
            
            response = self.scraper.get(trademo_url, timeout=10)
            if response.status_code == 200 and company.lower() in response.text.lower():
                results.append({
                    'title': f"Trademo - {company}",
                    'url': trademo_url,
                    'snippet': f"Trademo'da {company} şirketi bulundu",
                    'domain': 'trademo.com',
                    'full_text': response.text
                })
                print("   ✅ Trademo'da şirket bulundu")
        except Exception as e:
            print(f"   ❌ Trademo hatası: {e}")
        
        # Eximpedia hızlı kontrol
        try:
            eximpedia_url = f"https://www.eximpedia.app/search?q={quote(company)}"
            print(f"   🔎 Eximpedia kontrol...")
            
            response = self.scraper.get(eximpedia_url, timeout=10)
            if response.status_code == 200 and company.lower() in response.text.lower():
                results.append({
                    'title': f"Eximpedia - {company}",
                    'url': eximpedia_url,
                    'snippet': f"Eximpedia'da {company} şirketi bulundu",
                    'domain': 'eximpedia.app',
                    'full_text': response.text
                })
                print("   ✅ Eximpedia'da şirket bulundu")
        except Exception as e:
            print(f"   ❌ Eximpedia hatası: {e}")
        
        return results
    
    def _simple_google_search(self, company, country):
        """Basit Google araması"""
        results = []
        queries = [
            f'"{company}" "{country}" export',
            f'"{company}" "{country}" Russia',
        ]
        
        for query in queries:
            try:
                print(f"   🔎 Google: {query}")
                
                url = "https://www.google.com/search"
                params = {"q": query, "num": 2}
                headers = {
                    'User-Agent': random.choice(self.config.USER_AGENTS),
                }
                
                response = self.scraper.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    page_results = self._parse_google_simple(response.text)
                    results.extend(page_results)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Google hatası: {e}")
                continue
        
        return results
    
    def _parse_google_simple(self, html):
        """Basit Google parser"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Çeşitli Google formatları
        for result in soup.find_all('div', class_=['g', 'rc', 'tF2Cxc']):
            try:
                title_elem = result.find('h3') or result.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text()
                link_elem = result.find('a')
                url = link_elem.get('href') if link_elem else ""
                
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]
                
                snippet_elem = result.find('div', class_=['VwiC3b', 's'])
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                if url and url.startswith('http'):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'domain': self._extract_domain(url),
                        'full_text': f"{title} {snippet}"
                    })
                    
            except Exception:
                continue
        
        return results
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            return urlparse(url).netloc
        except:
            return ""

class FastAnalyzer:
    def __init__(self, config):
        self.config = config
        self.sanctioned_codes = ['8708', '8711', '8703']
    
    def fast_analyze(self, search_results, company, country):
        """Hızlı analiz"""
        print(f"🔍 HIZLI ANALİZ: {len(search_results)} sonuç")
        
        analyzed_results = []
        
        for result in search_results:
            analysis = self._analyze_single_fast(result, company, country)
            if analysis:
                analyzed_results.append(analysis)
        
        return analyzed_results
    
    def _analyze_single_fast(self, result, company, country):
        """Tekil sonucu hızlı analiz et"""
        try:
            domain = result.get('domain', '')
            full_text = result.get('full_text', '')
            text_lower = full_text.lower()
            
            # Ülke bağlantısı
            country_found = self._detect_country_fast(text_lower, domain)
            
            # GTIP kodları
            gtip_codes = self._extract_gtip_fast(text_lower)
            
            # Yaptırım kontrolü
            sanctioned_gtips = [code for code in gtip_codes if code in self.sanctioned_codes]
            
            # Güven seviyesi
            confidence = self._calculate_confidence_fast(country_found, gtip_codes, sanctioned_gtips, domain)
            
            # Risk analizi
            risk_data = self._assess_risk_fast(country_found, gtip_codes, sanctioned_gtips, company, country, confidence)
            
            return {
                **risk_data,
                'BAŞLIK': result.get('title', ''),
                'URL': result.get('url', ''),
                'ÖZET': result.get('snippet', ''),
                'KAYNAK_DOMAIN': domain,
                'GÜVEN_SEVİYESİ': f"%{confidence}",
            }
            
        except Exception as e:
            print(f"   ❌ Analiz hatası: {e}")
            return None
    
    def _detect_country_fast(self, text_lower, domain):
        """Hızlı ülke tespiti"""
        # Temel pattern'ler
        patterns = [
            'russia', 'rusya', 'russian',
            'destination russia', 
            'country of export russia',
            'export russia',
            'import russia'
        ]
        
        for pattern in patterns:
            if pattern in text_lower:
                return True
        
        return False
    
    def _extract_gtip_fast(self, text_lower):
        """Hızlı GTIP çıkarma"""
        codes = set()
        
        # 4 haneli kodlar
        four_digit = re.findall(r'\b\d{4}\b', text_lower)
        codes.update(four_digit)
        
        # HS Code pattern
        hs_matches = re.findall(r'hs code.*?(\d{4})', text_lower, re.IGNORECASE)
        codes.update(hs_matches)
        
        # Otomatik 8708
        if '8708' in text_lower or 'vehicle' in text_lower:
            codes.add('8708')
        
        return list(codes)
    
    def _calculate_confidence_fast(self, country_found, gtip_codes, sanctioned_gtips, domain):
        """Hızlı güven hesaplama"""
        confidence = 0
        
        if any(site in domain for site in ['trademo.com', 'eximpedia.app']):
            confidence += 40
        
        if country_found:
            confidence += 30
        
        if gtip_codes:
            confidence += 20
        
        if sanctioned_gtips:
            confidence += 10
        
        return min(confidence, 100)
    
    def _assess_risk_fast(self, country_found, gtip_codes, sanctioned_gtips, company, country, confidence):
        """Hızlı risk değerlendirmesi"""
        if sanctioned_gtips:
            status = "YÜKSEK_RİSK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ticaret"
            advice = f"⛔ ACİL! Yaptırımlı GTIP: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif country_found and gtip_codes:
            status = "ORTA_RİSK"
            explanation = f"🟡 ORTA RİSK: {company} şirketinin {country} ile ticareti var"
            advice = f"GTIP: {', '.join(gtip_codes)} - İnceleme önerilir"
            risk_level = "ORTA"
        elif country_found:
            status = "DÜŞÜK_RİSK"
            explanation = f"🟢 DÜŞÜK RİSK: {company} şirketinin {country} ile bağlantısı var"
            advice = "Ticaret bağlantısı bulundu"
            risk_level = "DÜŞÜK"
        else:
            status = "TEMİZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile bağlantısı yok"
            advice = "Risk bulunamadı"
            risk_level = "YOK"
        
        return {
            'ŞİRKET': company,
            'ÜLKE': country,
            'DURUM': status,
            'AI_AÇIKLAMA': explanation,
            'AI_TAVSIYE': advice,
            'YAPTIRIM_RİSKİ': risk_level,
            'TESPİT_EDİLEN_GTİPLER': ', '.join(gtip_codes),
            'YAPTIRIMLI_GTİPLER': ', '.join(sanctioned_gtips),
            'ULKE_BAGLANTISI': 'EVET' if country_found else 'HAYIR',
        }

def create_simple_excel(results, company, country):
    """Basit Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RİSKİ', 'ULKE_BAGLANTISI',
            'TESPİT_EDİLEN_GTİPLER', 'YAPTIRIMLI_GTİPLER', 'GÜVEN_SEVİYESİ',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            ws.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws.cell(row=row, column=4, value=str(result.get('YAPTIRIM_RİSKİ', '')))
            ws.cell(row=row, column=5, value=str(result.get('ULKE_BAGLANTISI', '')))
            ws.cell(row=row, column=6, value=str(result.get('TESPİT_EDİLEN_GTİPLER', '')))
            ws.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTİPLER', '')))
            ws.cell(row=row, column=8, value=str(result.get('GÜVEN_SEVİYESİ', '')))
            ws.cell(row=row, column=9, value=str(result.get('AI_AÇIKLAMA', '')))
            ws.cell(row=row, column=10, value=str(result.get('AI_TAVSIYE', '')))
            ws.cell(row=row, column=11, value=str(result.get('BAŞLIK', '')))
            ws.cell(row=row, column=12, value=str(result.get('URL', '')))
        
        # Stil ayarları
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
        
        wb.save(filename)
        print(f"✅ Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel hatası: {e}")
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
        if not data:
            return jsonify({"error": "Geçersiz JSON verisi"}), 400
            
        company = data.get('company', '').strip()
        country = data.get('country', '').strip()
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        logging.info(f"🚀 ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = AdvancedConfig()
        searcher = SmartSearchEngine(config)
        analyzer = FastAnalyzer(config)
        
        # Arama yap
        search_results = searcher.quick_search(company, country)
        
        # Analiz et
        if search_results:
            analyzed_results = analyzer.fast_analyze(search_results, company, country)
        else:
            analyzed_results = [{
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'TEMİZ',
                'AI_AÇIKLAMA': f'✅ {company} şirketinin {country} ile ticaret bağlantısı bulunamadı',
                'AI_TAVSIYE': 'Risk tespit edilmedi',
                'YAPTIRIM_RİSKİ': 'YOK',
                'TESPİT_EDİLEN_GTİPLER': '',
                'YAPTIRIMLI_GTİPLER': '',
                'ULKE_BAGLANTISI': 'HAYIR',
                'BAŞLIK': 'Temiz Sonuç',
                'URL': '',
                'KAYNAK_DOMAIN': 'Sistem',
                'GÜVEN_SEVİYESİ': '%85'
            }]
        
        # Excel oluştur
        excel_filepath = create_simple_excel(analyzed_results, company, country)
        
        execution_time = time.time() - start_time
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
            "execution_time": f"{execution_time:.2f}s",
            "total_results": len(analyzed_results),
            "analysis": analyzed_results,
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
        
        if os.path.exists(filename):
            return send_file(
                filename,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({"error": "Excel dosyası bulunamadı"}), 404
            
    except Exception as e:
        logging.error(f"❌ İndirme hatası: {e}")
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "message": "Ticaret Analiz Sistemi Çalışıyor"
    })

# Basit test endpoint'i
@app.route('/test')
def test():
    return jsonify({
        "message": "Backend çalışıyor!",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
