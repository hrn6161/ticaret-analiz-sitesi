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

print("🚀 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3
        self.REQUEST_TIMEOUT = 15
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
    
    def smart_crawl(self, url, target_country):
        """Akıllı crawl"""
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
        """İçerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            country_found = target_country.lower() in text_lower
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
        
        return list(all_codes)[:10]

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
        self.sanction_cache = {}
    
    def quick_check_gtip(self, gtip_codes):
        """Hızlı GTIP kontrolü"""
        if not gtip_codes:
            return []
            
        sanctioned_codes = []
        checked_codes = gtip_codes[:self.config.MAX_GTIP_CHECK]
        
        for gtip_code in checked_codes:
            if gtip_code in self.sanction_cache:
                if self.sanction_cache[gtip_code]:
                    sanctioned_codes.append(gtip_code)
                continue
                
            try:
                url = "https://eur-lex.europa.eu/search.html"
                params = {
                    'text': f'"{gtip_code}" sanction prohibited',
                    'type': 'advanced',
                    'lang': 'en'
                }
                
                response = requests.get(url, params=params, timeout=8)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.get_text().lower()
                    
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

class AITradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = FastSearcher(config)
        self.crawler = SmartCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
    
    def analyze_company_country(self, company, country):
        """Şirket-ülke analizi"""
        logging.info(f"🤖 AI ANALİZ: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business"
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                logging.info(f"🔍 Sorgu {i}/2: {query}")
                
                search_results = self.searcher.fast_search(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    continue
                
                for j, result in enumerate(search_results, 1):
                    logging.info(f"📄 Sonuç {j}: {result['title'][:50]}...")
                    
                    crawl_result = self.crawler.smart_crawl(result['url'], country)
                    
                    if not crawl_result['gtip_codes']:
                        snippet_gtips = self.crawler.extract_gtip_codes(result['full_text'])
                        if snippet_gtips:
                            crawl_result['gtip_codes'] = snippet_gtips
                    
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    analysis = self.create_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips
                    )
                    
                    all_results.append(analysis)
                
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
            'CONTENT_PREVIEW': crawl_result['content_preview'],
            'STATUS_CODE': crawl_result.get('status_code', 'N/A'),
            'KAYNAK_URL': search_result['url']
        }

def create_detailed_excel_report(results, company, country):
    """Detaylı Excel raporu - orijinal formata uygun"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        wb = Workbook()
        
        # 1. Sayfa: Analiz Sonuçları
        ws1 = wb.active
        ws1.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA',
            'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET', 'STATUS_CODE'
        ]
        
        for col, header in enumerate(headers, 1):
            ws1.cell(row=1, column=col, value=header).font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            ws1.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws1.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws1.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws1.cell(row=row, column=4, value=str(result.get('YAPTIRIM_RISKI', '')))
            ws1.cell(row=row, column=5, value=str(result.get('ULKE_BAGLANTISI', '')))
            ws1.cell(row=row, column=6, value=str(result.get('TESPIT_EDILEN_GTIPLER', '')))
            ws1.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTIPLER', '')))
            ws1.cell(row=row, column=8, value=str(result.get('AI_AÇIKLAMA', '')))
            ws1.cell(row=row, column=9, value=str(result.get('AI_TAVSIYE', '')))
            ws1.cell(row=row, column=10, value=str(result.get('BAŞLIK', '')))
            ws1.cell(row=row, column=11, value=str(result.get('URL', '')))
            ws1.cell(row=row, column=12, value=str(result.get('ÖZET', '')))
            ws1.cell(row=row, column=13, value=str(result.get('STATUS_CODE', '')))
        
        # 2. Sayfa: Yapay Zeka Özeti
        ws2 = wb.create_sheet("🤖 YAPAY ZEKA TİCARET ANALİZ YORUMU")
        
        # Başlık
        ws2.merge_cells('A1:H1')
        ws2['A1'] = "🤖 YAPAY ZEKA TİCARET ANALİZ YORUMU"
        ws2['A1'].font = Font(bold=True, size=16)
        
        # Şirket ve Ülke Bilgisi
        ws2['A3'] = "ŞİRKET:"
        ws2['B3'] = company
        ws2['A4'] = "ÜLKE:"
        ws2['B4'] = country
        ws2['A5'] = "ANALİZ TARİHİ:"
        ws2['B5'] = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Özet Bilgiler
        ws2['A7'] = "TOPLAM SONUÇ:"
        ws2['B7'] = len(results)
        
        high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
        medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
        country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
        
        ws2['A8'] = "YÜKSEK RİSK:"
        ws2['B8'] = high_risk_count
        ws2['A9'] = "ORTA RİSK:"
        ws2['B9'] = medium_risk_count
        ws2['A10'] = "ÜLKE BAĞLANTISI:"
        ws2['B10'] = country_connection_count
        
        # Yapay Zeka Yorumu
        ws2['A12'] = "🤖 YAPAY ZEKA ANALİZ YORUMU:"
        ws2['A12'].font = Font(bold=True)
        
        if high_risk_count > 0:
            yorum = f"⛔ KRİTİK RİSK! {company} şirketinin {country} ile yaptırımlı ürün ticareti tespit edildi. "
            yorum += f"Toplam {high_risk_count} farklı kaynakta yaptırımlı GTIP kodları bulundu. "
            yorum += "Acil önlem alınması gerekmektedir."
        elif medium_risk_count > 0:
            yorum = f"🟡 ORTA RİSK! {company} şirketinin {country} ile ticaret bağlantısı bulundu. "
            yorum += f"{medium_risk_count} farklı kaynakta ticaret ilişkisi doğrulandı. "
            yorum += "Detaylı inceleme önerilir."
        elif country_connection_count > 0:
            yorum = f"🟢 DÜŞÜK RİSK! {company} şirketinin {country} ile bağlantısı bulundu ancak yaptırım riski tespit edilmedi. "
            yorum += "Standart ticaret prosedürleri uygulanabilir."
        else:
            yorum = f"✅ TEMİZ! {company} şirketinin {country} ile ticaret bağlantısı bulunamadı. "
            yorum += "Herhangi bir yaptırım riski tespit edilmedi."
        
        ws2['A13'] = yorum
        
        # Tavsiyeler
        ws2['A15'] = "💡 YAPAY ZEKA TAVSİYELERİ:"
        ws2['A15'].font = Font(bold=True)
        
        if high_risk_count > 0:
            tavsiye = "1. ⛔ Yaptırımlı ürün ihracından acilen kaçının\n"
            tavsiye += "2. 🔍 Yasal danışmanla görüşün\n"
            tavsiye += "3. 📊 Ticaret partnerlerini yeniden değerlendirin\n"
            tavsiye += "4. 🚨 Uyum birimini bilgilendirin"
        elif medium_risk_count > 0:
            tavsiye = "1. 🔍 Detaylı due diligence yapın\n"
            tavsiye += "2. 📋 Ticaret dokümanlarını kontrol edin\n"
            tavsiye += "3. 🌐 Güncel yaptırım listelerini takip edin\n"
            tavsiye += "4. 💼 Alternatif pazarları değerlendirin"
        else:
            tavsiye = "1. ✅ Standart ticaret prosedürlerine devam edin\n"
            tavsiye += "2. 📈 Pazar araştırmalarını sürdürün\n"
            tavsiye += "3. 🔄 Düzenli olarak kontrol edin\n"
            tavsiye += "4. 🌍 Yeni iş fırsatlarını değerlendirin"
        
        ws2['A16'] = tavsiye
        
        # Kaynaklar
        ws2['A18'] = "🔍 ANALİZ EDİLEN KAYNAKLAR:"
        ws2['A18'].font = Font(bold=True)
        
        for i, result in enumerate(results[:5], 1):  # İlk 5 kaynak
            ws2[f'A{19 + i}'] = f"{i}. {result.get('BAŞLIK', '')}"
            ws2[f'B{19 + i}'] = result.get('URL', '')
        
        # Stil ayarları
        for row in range(1, 25):
            for col in range(1, 9):
                cell = ws2.cell(row=row, column=col)
                if row in [1, 12, 15, 18]:
                    cell.font = Font(bold=True)
        
        # Kolon genişlikleri
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
        
        ws2.column_dimensions['A'].width = 30
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
        
        logging.info(f"🚀 AI ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = Config()
        analyzer = AITradeAnalyzer(config)
        
        results = analyzer.analyze_company_country(company, country)
        
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
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
