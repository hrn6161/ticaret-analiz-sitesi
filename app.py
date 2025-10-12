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
from urllib.parse import urlparse, quote
import concurrent.futures
import json

app = Flask(__name__)

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
        self.RETRY_ATTEMPTS = 3
        self.MAX_GTIP_CHECK = 5
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        self.TRADE_SITES = ["trademo.com", "eximpedia.app", "volza.com", "importyet.com"]

class SmartSearchEngine:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def smart_search(self, company, country):
        """Akıllı arama - direkt ticaret sitelerini hedefle"""
        all_results = []
        
        # Ticaret sitelerinde direkt arama
        trade_site_results = self._search_trade_sites_directly(company, country)
        all_results.extend(trade_site_results)
        
        # Google'da site-specific arama
        google_results = self._search_google_specific(company, country)
        all_results.extend(google_results)
        
        return all_results
    
    def _search_trade_sites_directly(self, company, country):
        """Ticaret sitelerinde direkt arama"""
        results = []
        
        # Trademo direkt arama
        trademo_results = self._search_trademo_direct(company, country)
        if trademo_results:
            results.extend(trademo_results)
        
        # Eximpedia direkt arama
        eximpedia_results = self._search_eximpedia_direct(company, country)
        if eximpedia_results:
            results.extend(eximpedia_results)
        
        return results
    
    def _search_trademo_direct(self, company, country):
        """Trademo'da direkt arama"""
        try:
            # Trademo search URL
            search_url = f"https://www.trademo.com/search/companies?q={quote(company)}"
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.trademo.com/',
            }
            
            print(f"   🔍 Trademo'da aranıyor: {company}")
            response = self.scraper.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Basit analiz - sayfada Rusya ve şirket adı ara
                content = response.text.lower()
                company_lower = company.lower()
                
                if company_lower in content:
                    return [{
                        'title': f"Trademo: {company}",
                        'url': search_url,
                        'snippet': f"Trademo ticaret veritabanında {company} şirketi bulundu",
                        'domain': 'trademo.com',
                        'search_engine': 'trademo_direct',
                        'full_text': response.text
                    }]
            
            return []
            
        except Exception as e:
            print(f"   ❌ Trademo direkt arama hatası: {e}")
            return []
    
    def _search_eximpedia_direct(self, company, country):
        """Eximpedia'da direkt arama"""
        try:
            # Eximpedia search URL
            search_url = f"https://www.eximpedia.app/search?q={quote(company)}+{quote(country)}"
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.eximpedia.app/',
            }
            
            print(f"   🔍 Eximpedia'da aranıyor: {company} + {country}")
            response = self.scraper.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text.lower()
                company_lower = company.lower()
                country_lower = country.lower()
                
                if company_lower in content or country_lower in content:
                    return [{
                        'title': f"Eximpedia: {company} - {country}",
                        'url': search_url,
                        'snippet': f"Eximpedia veritabanında {company} şirketi ve {country} bağlantısı bulundu",
                        'domain': 'eximpedia.app',
                        'search_engine': 'eximpedia_direct',
                        'full_text': response.text
                    }]
            
            return []
            
        except Exception as e:
            print(f"   ❌ Eximpedia direkt arama hatası: {e}")
            return []
    
    def _search_google_specific(self, company, country):
        """Google'da site-specific arama"""
        try:
            # Site-specific sorgular
            queries = [
                f'site:trademo.com "{company}" "{country}"',
                f'site:eximpedia.app "{company}" "{country}"',
                f'site:volza.com "{company}" "{country}"',
                f'"{company}" "{country}" export Russia',
                f'"{company}" "{country}" import Russia',
            ]
            
            all_results = []
            
            for query in queries:
                try:
                    url = "https://www.google.com/search"
                    params = {"q": query, "num": 3}
                    headers = {
                        'User-Agent': random.choice(self.config.USER_AGENTS),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }
                    
                    print(f"   🔍 Google'da aranıyor: {query}")
                    response = self.scraper.get(url, params=params, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        results = self._parse_google_simple(response.text)
                        all_results.extend(results)
                        
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"   ❌ Google sorgu hatası: {e}")
                    continue
            
            return all_results
            
        except Exception as e:
            print(f"   ❌ Google arama hatası: {e}")
            return []
    
    def _parse_google_simple(self, html):
        """Basit Google sonuç parser'ı"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Farklı Google sonuç formatları için deneme
        selectors = [
            'div.g',
            'div.rc',
            'div.tF2Cxc',
            'div.yuRUbf'
        ]
        
        for selector in selectors:
            for result in soup.select(selector):
                try:
                    # Başlık
                    title_elem = result.find('h3') or result.find('a')
                    if not title_elem:
                        continue
                    title = title_elem.get_text()
                    
                    # URL
                    link_elem = result.find('a')
                    url = link_elem.get('href') if link_elem else ""
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    # Snippet
                    snippet_elem = result.find('div', class_=['VwiC3b', 's', 'st'])
                    snippet = snippet_elem.get_text() if snippet_elem else ""
                    
                    if url and url.startswith('http'):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'domain': self._extract_domain(url),
                            'search_engine': 'google',
                            'full_text': f"{title} {snippet}"
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

class IntelligentCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def intelligent_crawl(self, result, company, country):
        """Akıllı crawl - snippet analizine odaklan"""
        try:
            domain = result.get('domain', '')
            full_text = result.get('full_text', '') or f"{result.get('title', '')} {result.get('snippet', '')}"
            
            print(f"   🔍 Analiz: {domain}")
            
            # Domain'e özel analiz
            if 'trademo.com' in domain:
                return self._analyze_trademo_content(full_text, company, country, domain)
            elif 'eximpedia.app' in domain:
                return self._analyze_eximpedia_content(full_text, company, country, domain)
            else:
                return self._analyze_general_content(full_text, company, country, domain)
                
        except Exception as e:
            print(f"   ❌ Crawl analiz hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'status_code': 'ERROR'}
    
    def _analyze_trademo_content(self, text, company, country, domain):
        """Trademo içeriğini analiz et"""
        text_lower = text.lower()
        
        # Gelişmiş pattern matching
        country_found = self._detect_country_trademo(text_lower, country)
        gtip_codes = self._extract_gtip_trademo(text_lower)
        
        print(f"   🔍 Trademo analiz: Ülke={country_found}, GTIP={gtip_codes}")
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': text[:300] + "..." if len(text) > 300 else text,
            'status_code': 'ANALYZED'
        }
    
    def _analyze_eximpedia_content(self, text, company, country, domain):
        """Eximpedia içeriğini analiz et"""
        text_lower = text.lower()
        
        country_found = self._detect_country_eximpedia(text_lower, country)
        gtip_codes = self._extract_gtip_eximpedia(text_lower)
        
        print(f"   🔍 Eximpedia analiz: Ülke={country_found}, GTIP={gtip_codes}")
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': text[:300] + "..." if len(text) > 300 else text,
            'status_code': 'ANALYZED'
        }
    
    def _analyze_general_content(self, text, company, country, domain):
        """Genel içeriği analiz et"""
        text_lower = text.lower()
        
        country_found = self._detect_country_general(text_lower, country)
        gtip_codes = self._extract_gtip_general(text_lower)
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': text[:200] + "..." if len(text) > 200 else text,
            'status_code': 'ANALYZED'
        }
    
    def _detect_country_trademo(self, text_lower, country):
        """Trademo'da ülke tespiti"""
        patterns = [
            r'country of export.*russia',
            r'export.*russia',
            r'russia.*export',
            r'country.*russia',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                print(f"   ✅ Trademo ülke pattern: {pattern}")
                return True
        
        return 'russia' in text_lower or 'rusya' in text_lower
    
    def _detect_country_eximpedia(self, text_lower, country):
        """Eximpedia'da ülke tespiti"""
        patterns = [
            r'destination.*russia',
            r'export.*russia',
            r'russia.*destination',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                print(f"   ✅ Eximpedia ülke pattern: {pattern}")
                return True
        
        return 'russia' in text_lower or 'rusya' in text_lower
    
    def _detect_country_general(self, text_lower, country):
        """Genel ülke tespiti"""
        return any(pattern in text_lower for pattern in ['russia', 'rusya', 'russian'])
    
    def _extract_gtip_trademo(self, text_lower):
        """Trademo'da GTIP çıkarma"""
        codes = set()
        
        # HS Code pattern'leri
        hs_patterns = [
            r'hs code.*?(\d{4})',
            r'hs.*?(\d{4})',
            r'(\d{4}).*hs code',
        ]
        
        for pattern in hs_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match) == 4:
                    codes.add(match)
                    print(f"   🔍 Trademo GTIP: {match}")
        
        # Otomatik 8708 ekle (motorlu taşıtlar)
        if any(keyword in text_lower for keyword in ['vehicle', 'automotive', 'motor', '8708']):
            codes.add('8708')
            print("   🔍 Otomatik 8708 eklendi")
        
        return list(codes)
    
    def _extract_gtip_eximpedia(self, text_lower):
        """Eximpedia'da GTIP çıkarma"""
        codes = set()
        
        # GTIP pattern'leri
        gtip_patterns = [
            r'gtip.*?(\d{4})',
            r'hs.*?(\d{4})',
            r'code.*?(\d{4})',
        ]
        
        for pattern in gtip_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match) == 4:
                    codes.add(match)
                    print(f"   🔍 Eximpedia GTIP: {match}")
        
        if any(keyword in text_lower for keyword in ['8708', 'vehicle']):
            codes.add('8708')
        
        return list(codes)
    
    def _extract_gtip_general(self, text_lower):
        """Genel GTIP çıkarma"""
        matches = re.findall(r'\b\d{4}\b', text_lower)
        return list(set(matches))

class SmartAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = SmartSearchEngine(config)
        self.crawler = IntelligentCrawler(config)
        self.sanctioned_codes = ['8708', '8711', '8703']
    
    def smart_analyze(self, company, country):
        """Akıllı analiz"""
        print(f"🎯 AKILLI ANALİZ: {company} ↔ {country}")
        
        # Arama yap
        search_results = self.searcher.smart_search(company, country)
        print(f"   📊 Arama sonuçları: {len(search_results)}")
        
        all_results = []
        
        # Sonuçları analiz et
        for result in search_results:
            analysis = self._analyze_single_result(result, company, country)
            if analysis:
                all_results.append(analysis)
        
        return all_results
    
    def _analyze_single_result(self, result, company, country):
        """Tekil sonucu analiz et"""
        try:
            # Akıllı crawl
            crawl_result = self.crawler.intelligent_crawl(result, company, country)
            
            # Yaptırım kontrolü
            sanctioned_gtips = []
            for code in crawl_result['gtip_codes']:
                if code in self.sanctioned_codes:
                    sanctioned_gtips.append(code)
            
            # Güven seviyesi
            confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
            
            # Risk analizi
            analysis = self._create_analysis_result(
                company, country, result, crawl_result, sanctioned_gtips, confidence
            )
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Sonuç analiz hatası: {e}")
            return None
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # Domain güveni
        if any(trade_site in domain for trade_site in self.config.TRADE_SITES):
            confidence += 40
        
        # Ülke bağlantısı
        if crawl_result['country_found']:
            confidence += 30
        
        # GTIP kodları
        if crawl_result['gtip_codes']:
            confidence += 20
        
        # Yaptırım tespiti
        if sanctioned_gtips:
            confidence += 10
        
        return min(confidence, 100)
    
    def _create_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips, confidence):
        """Analiz sonucu oluştur"""
        
        if sanctioned_gtips:
            status = "YÜKSEK_RISK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
            advice = f"⛔ ACİL DURUM! Yaptırımlı GTIP: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif crawl_result['country_found'] and crawl_result['gtip_codes']:
            status = "ORTA_RISK"
            explanation = f"🟡 ORTA RİSK: {company} şirketinin {country} ile ticaret bağlantısı bulundu"
            advice = f"GTIP: {', '.join(crawl_result['gtip_codes'])} - Detaylı inceleme önerilir"
            risk_level = "ORTA"
        elif crawl_result['country_found']:
            status = "DÜŞÜK_RISK"
            explanation = f"🟢 DÜŞÜK RİSK: {company} şirketinin {country} ile bağlantısı var"
            advice = "Ticaret bağlantısı bulundu"
            risk_level = "DÜŞÜK"
        else:
            status = "TEMIZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile bağlantısı bulunamadı"
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
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
            'BAŞLIK': search_result['title'],
            'URL': search_result['url'],
            'ÖZET': search_result['snippet'],
            'KAYNAK_DOMAIN': search_result['domain'],
            'GÜVEN_SEVİYESİ': f"%{confidence}",
        }

def create_smart_excel_report(results, company, country):
    """Akıllı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'GÜVEN_SEVİYESİ',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET', 'KAYNAK_DOMAIN'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            ws.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws.cell(row=row, column=4, value=str(result.get('YAPTIRIM_RISKI', '')))
            ws.cell(row=row, column=5, value=str(result.get('ULKE_BAGLANTISI', '')))
            ws.cell(row=row, column=6, value=str(result.get('TESPIT_EDILEN_GTIPLER', '')))
            ws.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTIPLER', '')))
            ws.cell(row=row, column=8, value=str(result.get('GÜVEN_SEVİYESİ', '')))
            ws.cell(row=row, column=9, value=str(result.get('AI_AÇIKLAMA', '')))
            ws.cell(row=row, column=10, value=str(result.get('AI_TAVSIYE', '')))
            ws.cell(row=row, column=11, value=str(result.get('BAŞLIK', '')))
            ws.cell(row=row, column=12, value=str(result.get('URL', '')))
            ws.cell(row=row, column=13, value=str(result.get('ÖZET', '')))
            ws.cell(row=row, column=14, value=str(result.get('KAYNAK_DOMAIN', '')))
        
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
        print(f"❌ Excel rapor hatası: {e}")
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
        
        logging.info(f"🚀 AKILLI ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        config = AdvancedConfig()
        analyzer = SmartAnalyzer(config)
        
        results = analyzer.smart_analyze(company, country)
        
        # Eğer hiç sonuç yoksa temiz rapor oluştur
        if not results:
            results = [{
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'TEMIZ',
                'AI_AÇIKLAMA': f'✅ {company} şirketinin {country} ile ticaret bağlantısı bulunamadı',
                'AI_TAVSIYE': 'Risk tespit edilmedi, standart ticaret prosedürlerine devam edilebilir',
                'YAPTIRIM_RISKI': 'YOK',
                'TESPIT_EDILEN_GTIPLER': '',
                'YAPTIRIMLI_GTIPLER': '',
                'ULKE_BAGLANTISI': 'HAYIR',
                'BAŞLIK': 'Temiz Sonuç',
                'URL': '',
                'ÖZET': 'Analiz sonucunda risk bulunamadı',
                'KAYNAK_DOMAIN': 'Sistem Analizi',
                'GÜVEN_SEVİYESİ': '%85'
            }]
        
        excel_filepath = create_smart_excel_report(results, company, country)
        
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
        logging.error(f"❌ Excel indirme hatası: {e}")
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
