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
        ]

class SmartCrawler:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def smart_crawl(self, url, target_country, search_title, search_snippet):
        """Akıllı crawl - 403 alınırsa snippet analizine odaklan"""
        domain = self._extract_domain(url)
        
        # Trademo ve Eximpedia için özel işlem
        if any(site in domain for site in ['trademo.com', 'eximpedia.app']):
            logging.info(f"🎯 ÖZEL SITE ANALIZI: {domain}")
            return self._analyze_trade_sites(url, target_country, search_title, search_snippet, domain)
        
        # Diğer siteler için normal crawl
        return self._try_normal_crawl(url, target_country)
    
    def _analyze_trade_sites(self, url, target_country, search_title, search_snippet, domain):
        """Ticaret siteleri için özel analiz"""
        combined_text = f"{search_title} {search_snippet}".lower()
        
        logging.info(f"🔍 Ticaret sitesi snippet analizi: {domain}")
        
        # Gelişmiş ülke kontrolü
        country_found = self._check_country_deep(combined_text, target_country, domain)
        
        # Gelişmiş GTIP çıkarma
        gtip_codes = self._extract_gtip_smart(combined_text, domain)
        
        # Domain'e özel pattern'ler
        if 'trademo.com' in domain:
            country_found, gtip_codes = self._apply_trademo_patterns(combined_text, country_found, gtip_codes)
        elif 'eximpedia.app' in domain:
            country_found, gtip_codes = self._apply_eximpedia_patterns(combined_text, country_found, gtip_codes)
        
        logging.info(f"🔍 {domain} analiz sonucu: Ülke={country_found}, GTIP={gtip_codes}")
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes,
            'content_preview': f"{search_title} - {search_snippet}",
            'status_code': 'SMART_ANALYSIS'
        }
    
    def _check_country_deep(self, text_lower, target_country, domain):
        """Derinlemesine ülke kontrolü"""
        # Rusya için özel varyasyonlar
        russia_patterns = [
            'russia', 'rusya', 'russian', 'rusian', 'rus',
            'russian federation', 'russia country'
        ]
        
        # Ticaret terimleri ile birlikte kontrol
        trade_terms = [
            'export', 'import', 'country', 'origin', 'destination', 
            'trade', 'shipment', 'supplier', 'buyer', 'importer', 'exporter'
        ]
        
        # Eximpedia için özel kontrol
        if 'eximpedia.app' in domain:
            if any(pattern in text_lower for pattern in ['destination russia', 'export russia', 'russia destination']):
                logging.info("✅ Eximpedia: Destination Russia tespit edildi")
                return True
        
        # Trademo için özel kontrol
        if 'trademo.com' in domain:
            if any(pattern in text_lower for pattern in ['country of export russia', 'export country russia']):
                logging.info("✅ Trademo: Country of Export Russia tespit edildi")
                return True
        
        # Genel kontrol
        for country_pattern in russia_patterns:
            if country_pattern in text_lower:
                # Ticaret terimleriyle yakınlık kontrolü
                for term in trade_terms:
                    if f"{term} {country_pattern}" in text_lower or f"{country_pattern} {term}" in text_lower:
                        logging.info(f"✅ Ülke-trade bağlantısı: {term} {country_pattern}")
                        return True
                logging.info(f"✅ Ülke bulundu: {country_pattern}")
                return True
        
        return False
    
    def _extract_gtip_smart(self, text, domain):
        """Akıllı GTIP çıkarma"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',  # 8708.30 gibi
            r'\b\d{6}\b',  # 870830 gibi
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
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
                    logging.info(f"🔍 GTIP kodu bulundu: {code[:4]}")
        
        # Ticaret siteleri için otomatik 8708 ekle
        if any(site in domain for site in ['trademo.com', 'eximpedia.app']):
            if '8708' in text or '870830' in text:
                all_codes.add('8708')
                logging.info("🔍 Otomatik 8708 eklendi (ticaret sitesi)")
        
        return list(all_codes)
    
    def _apply_trademo_patterns(self, text_lower, current_country_found, current_gtip_codes):
        """Trademo için özel pattern'ler"""
        country_found = current_country_found
        gtip_codes = current_gtip_codes.copy()
        
        # Country of Export pattern
        if re.search(r'country of export.*russia', text_lower, re.IGNORECASE):
            country_found = True
            logging.info("🎯 Trademo: Country of Export Russia pattern")
        
        # HS Code pattern
        if re.search(r'hs code.*8708', text_lower, re.IGNORECASE) and '8708' not in gtip_codes:
            gtip_codes.append('8708')
            logging.info("🎯 Trademo: HS Code 8708 pattern")
        
        return country_found, gtip_codes
    
    def _apply_eximpedia_patterns(self, text_lower, current_country_found, current_gtip_codes):
        """Eximpedia için özel pattern'ler"""
        country_found = current_country_found
        gtip_codes = current_gtip_codes.copy()
        
        # Destination pattern
        if re.search(r'destination.*russia', text_lower, re.IGNORECASE):
            country_found = True
            logging.info("🎯 Eximpedia: Destination Russia pattern")
        
        return country_found, gtip_codes
    
    def _try_normal_crawl(self, url, target_country):
        """Normal crawl denemesi"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._parse_content(response.text, target_country, response.status_code)
            else:
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
        except Exception as e:
            logging.warning(f"❌ Crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_content(self, html, target_country, status_code):
        """İçerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            country_found = self._check_country_deep(text_lower, target_country, "")
            gtip_codes = self._extract_gtip_smart(text_content, "")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content,
                'status_code': status_code
            }
        except Exception as e:
            logging.error(f"❌ Parse hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'PARSE_ERROR'}
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class IntelligentSearcher:
    def __init__(self, config):
        self.config = config
        self.crawler = SmartCrawler(config)
    
    def intelligent_search(self, company, country):
        """Akıllı arama - firma ve ülkeye özel"""
        queries = self._generate_smart_queries(company, country)
        all_results = []
        
        for i, query in enumerate(queries, 1):
            try:
                logging.info(f"🔍 Sorgu {i}/{len(queries)}: {query}")
                
                if i > 1:
                    time.sleep(random.uniform(2, 4))
                
                search_results = self._duckduckgo_search(query)
                
                for result in search_results:
                    analysis = self._analyze_result(result, company, country)
                    if analysis:
                        all_results.append(analysis)
                
            except Exception as e:
                logging.error(f"❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _generate_smart_queries(self, company, country):
        """Akıllı sorgu oluşturma"""
        base_queries = [
            f'"{company}" "{country}" export',
            f'"{company}" "{country}" import', 
            f'"{company}" "{country}" trade',
            f'"{company}" "{country}" shipment',
            f'"{company}" "{country}" supplier',
        ]
        
        # Ticaret sitelerine özel sorgular
        trade_site_queries = [
            f'site:trademo.com "{company}" "{country}"',
            f'site:eximpedia.app "{company}" "{country}"',
            f'site:volza.com "{company}" "{country}"',
        ]
        
        return base_queries + trade_site_queries
    
    def _duckduckgo_search(self, query):
        """DuckDuckGo arama"""
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': '', 'kl': 'us-en'}
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                return self._parse_ddgo_results(response.text)
            return []
        except Exception as e:
            logging.error(f"❌ Arama hatası: {e}")
            return []
    
    def _parse_ddgo_results(self, html):
        """DuckDuckGo sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for div in soup.find_all('div', class_='result')[:self.config.MAX_RESULTS]:
            try:
                title_elem = div.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                
                # Redirect handling
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
                    'domain': self._extract_domain(url)
                })
                
            except Exception as e:
                logging.error(f"❌ Sonuç parse hatası: {e}")
                continue
        
        return results
    
    def _analyze_result(self, result, company, country):
        """Sonuç analizi"""
        try:
            # Akıllı crawl
            crawl_result = self.crawler.smart_crawl(
                result['url'], 
                country, 
                result['title'], 
                result['snippet']
            )
            
            # Domain filtresi - sadece güvenilir kaynaklar
            domain = result['domain']
            trusted_domains = ['trademo.com', 'eximpedia.app', 'volza.com', 'importyet.com']
            
            if not any(trusted in domain for trusted in trusted_domains):
                if not crawl_result['country_found']:
                    logging.info(f"🔍 Güvenilir olmayan domain atlandı: {domain}")
                    return None
            
            # Güven seviyesi
            confidence = self._calculate_confidence(crawl_result, domain)
            
            # Risk analizi
            risk_analysis = self._analyze_risk(crawl_result, company, country, confidence)
            
            return {
                **risk_analysis,
                'BAŞLIK': result['title'],
                'URL': result['url'],
                'ÖZET': result['snippet'],
                'GÜVEN_SEVİYESİ': f"%{confidence}",
                'KAYNAK_DOMAIN': domain
            }
            
        except Exception as e:
            logging.error(f"❌ Sonuç analiz hatası: {e}")
            return None
    
    def _calculate_confidence(self, crawl_result, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # Domain güveni
        if any(trusted in domain for trusted in ['trademo.com', 'eximpedia.app']):
            confidence += 40
        elif any(trusted in domain for trusted in ['volza.com', 'importyet.com']):
            confidence += 30
        
        # Ülke bağlantısı
        if crawl_result['country_found']:
            confidence += 30
        
        # GTIP kodları
        if crawl_result['gtip_codes']:
            confidence += 30
        
        return min(confidence, 100)
    
    def _analyze_risk(self, crawl_result, company, country, confidence):
        """Risk analizi"""
        if crawl_result['country_found'] and crawl_result['gtip_codes']:
            status = "RISK_VAR"
            explanation = f"🟡 RİSK: {company} şirketinin {country} ile ticaret bağlantısı bulundu"
            ai_tavsiye = f"GTIP kodları: {', '.join(crawl_result['gtip_codes'])} - Detaylı inceleme önerilir"
            risk_level = "ORTA"
        elif crawl_result['country_found']:
            status = "İLİŞKİ_VAR"
            explanation = f"🟢 İLİŞKİ: {company} şirketinin {country} ile bağlantısı var"
            ai_tavsiye = "Ticaret bağlantısı bulundu ancak GTIP kodu tespit edilemedi"
            risk_level = "DÜŞÜK"
        else:
            status = "TEMIZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile ticaret bağlantısı bulunamadı"
            ai_tavsiye = "Risk tespit edilmedi"
            risk_level = "YOK"
        
        return {
            'ŞİRKET': company,
            'ÜLKE': country,
            'DURUM': status,
            'AI_AÇIKLAMA': explanation,
            'AI_TAVSIYE': ai_tavsiye,
            'YAPTIRIM_RISKI': risk_level,
            'TESPIT_EDILEN_GTIPLER': ', '.join(crawl_result['gtip_codes']),
            'ULKE_BAGLANTISI': 'EVET' if crawl_result['country_found'] else 'HAYIR',
        }
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

class QuickSanctionChecker:
    def __init__(self):
        self.sanctioned_codes = ['8708', '8711', '8703']  # Örnek yaptırımlı kodlar
    
    def check_sanctions(self, gtip_codes):
        """Yaptırım kontrolü"""
        sanctioned = []
        for code in gtip_codes[:3]:  # İlk 3 kodu kontrol et
            if code in self.sanctioned_codes:
                sanctioned.append(code)
        return sanctioned

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
        
        config = Config()
        searcher = IntelligentSearcher(config)
        sanction_checker = QuickSanctionChecker()
        
        results = searcher.intelligent_search(company, country)
        
        # Yaptırım kontrolü
        for result in results:
            gtip_codes = result.get('TESPIT_EDILEN_GTIPLER', '').split(', ')
            if gtip_codes and gtip_codes != ['']:
                sanctioned = sanction_checker.check_sanctions(gtip_codes)
                if sanctioned:
                    result['YAPTIRIMLI_GTIPLER'] = ', '.join(sanctioned)
                    result['YAPTIRIM_RISKI'] = 'YÜKSEK'
                    result['DURUM'] = 'YAPTIRIMLI_RISK'
                    result['AI_AÇIKLAMA'] = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
                    result['AI_TAVSIYE'] = f"⛔ ACİL DURUM! Yaptırımlı GTIP kodları: {', '.join(sanctioned)}"
        
        execution_time = time.time() - start_time
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
            "execution_time": f"{execution_time:.2f}s",
            "total_results": len(results),
            "analysis": results
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"❌ Analiz hatası: {e}")
        return jsonify({"error": f"Sunucu hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
