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

print("🚀 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

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
        self.MAX_RESULTS = 3
        self.REQUEST_TIMEOUT = 15
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class AdvancedCrawler:
    def __init__(self, config):
        self.config = config
    
    def advanced_crawl(self, url, target_country):
        """Gelişmiş crawl - snippet derinlemesine analiz"""
        print(f"   🌐 Crawl: {url[:60]}...")
        
        # Önce sayfayı dene
        page_result = self._try_page_crawl(url, target_country)
        if page_result['status_code'] == 200:
            return page_result
        
        # Sayfa başarısızsa, snippet'i derinlemesine analiz et
        print(f"   🔍 Snippet derinlemesine analiz: {url}")
        return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'SNIPPET_ANALYSIS'}
    
    def _try_page_crawl(self, url, target_country):
        """Sayfa crawl dene"""
        try:
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return self._parse_advanced_content(response.text, target_country, response.status_code)
            else:
                print(f"   ❌ Sayfa hatası: {response.status_code}")
                return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': response.status_code}
        except Exception as e:
            print(f"   ❌ Sayfa crawl hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'ERROR'}
    
    def _parse_advanced_content(self, html, target_country, status_code):
        """Gelişmiş içerik analizi"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            text_lower = text_content.lower()
            
            # Gelişmiş ülke kontrolü
            country_found = self._check_country_advanced(text_lower, target_country)
            
            # Gelişmiş GTIP kod çıkarma
            gtip_codes = self.extract_advanced_gtip_codes(text_content)
            
            print(f"   🔍 Sayfa analizi: Ülke={country_found}, GTIP={gtip_codes[:5]}")
            
            return {
                'country_found': country_found,
                'gtip_codes': gtip_codes,
                'content_preview': text_content[:300] + "..." if len(text_content) > 300 else text_content,
                'status_code': status_code
            }
        except Exception as e:
            print(f"   ❌ Parse hatası: {e}")
            return {'country_found': False, 'gtip_codes': [], 'content_preview': '', 'status_code': 'PARSE_ERROR'}
    
    def _check_country_advanced(self, text_lower, target_country):
        """Gelişmiş ülke kontrolü"""
        country_variations = [
            target_country.lower(),
            target_country.upper(), 
            target_country.title(),
            'russia', 'rusya', 'rusian', 'rus'  # Rusya için özel varyasyonlar
        ]
        
        # Ticaret terimleri ile birlikte kontrol
        trade_terms = ['export', 'import', 'country', 'origin', 'destination', 'trade']
        
        for country_var in country_variations:
            if country_var in text_lower:
                # Ülke ismi geçiyorsa, ticaret terimleriyle yakınlık kontrolü
                for term in trade_terms:
                    if f"{term} {country_var}" in text_lower or f"{country_var} {term}" in text_lower:
                        print(f"   ✅ Ülke bağlantısı bulundu: {term} {country_var}")
                        return True
                print(f"   ✅ Ülke bağlantısı bulundu: {country_var}")
                return True
        
        return False
    
    def extract_advanced_gtip_codes(self, text):
        """Gelişmiş GTIP kod çıkarma"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',  # 8708.30 gibi
            r'\b\d{6}\b',  # 870830 gibi
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
            r'\bHarmonized\s?System\s?Code\s?:?\s?(\d{4,8})\b',
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Noktayı kaldır ve ilk 4 haneyi al
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    all_codes.add(code[:4])
                    print(f"   🔍 GTIP kodu bulundu: {code[:4]} (orijinal: {match})")
        
        return list(all_codes)
    
    def analyze_snippet_deep(self, snippet_text, target_country):
        """Snippet derinlemesine analizi - TRADEMO.COM için özel"""
        if not snippet_text:
            return {'country_found': False, 'gtip_codes': []}
        
        text_lower = snippet_text.lower()
        print(f"   🔍 Snippet analizi: {snippet_text[:100]}...")
        
        # Gelişmiş ülke kontrolü
        country_found = self._check_country_advanced(text_lower, target_country)
        
        # Gelişmiş GTIP çıkarma
        gtip_codes = self.extract_advanced_gtip_codes(snippet_text)
        
        # Özel pattern'ler için kontrol - TRADEMO.COM için
        special_patterns = [
            (r'country of export.*russia', 'russia', 'country_found'),
            (r'export.*russia', 'russia', 'country_found'), 
            (r'hs code.*8708', '8708', 'gtip'),
            (r'8708.*hs code', '8708', 'gtip'),
            (r'870830', '8708', 'gtip'),  # 6 haneli HS code
            (r'8708\.30', '8708', 'gtip'),  # Noktalı HS code
        ]
        
        for pattern, value, pattern_type in special_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if pattern_type == 'gtip' and value not in gtip_codes:
                    gtip_codes.append(value)
                    print(f"   🔍 Özel pattern GTIP: {value} ({pattern})")
                elif pattern_type == 'country_found' and not country_found:
                    country_found = True
                    print(f"   🔍 Özel pattern ülke: {value} ({pattern})")
        
        print(f"   🔍 Snippet analizi sonucu: Ülke={country_found}, GTIP={gtip_codes}")
        
        return {
            'country_found': country_found,
            'gtip_codes': gtip_codes
        }

class EnhancedSearcher:
    def __init__(self, config):
        self.config = config
        self.crawler = AdvancedCrawler(config)
    
    def enhanced_search(self, query, max_results=3):
        """Gelişmiş arama - snippet analizi ile"""
        try:
            print(f"   🔍 DuckDuckGo: {query}")
            
            headers = {'User-Agent': random.choice(self.config.USER_AGENTS)}
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': '', 'kl': 'us-en'}
            
            response = requests.post(url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                results = self.parse_enhanced_results(response.text, max_results)
                print(f"   ✅ {len(results)} sonuç bulundu")
                return results
            else:
                print(f"   ❌ DuckDuckGo hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"   ❌ Arama hatası: {e}")
            return []
    
    def parse_enhanced_results(self, html, max_results):
        """Gelişmiş sonuç parse"""
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
                
                # Snippet derinlemesine analiz
                combined_text = f"{title} {snippet}"
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'full_text': combined_text,
                    'domain': self._extract_domain(url)
                })
                
                print(f"      📄 Bulunan: {title[:60]}...")
                print(f"      🌐 Domain: {self._extract_domain(url)}")
                
            except Exception as e:
                print(f"      ❌ Sonuç parse hatası: {e}")
                continue
        
        return results
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

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
        
        print(f"   🔍 EUR-Lex kontrolü: {checked_codes}")
        
        for gtip_code in checked_codes:
            if gtip_code in self.sanction_cache:
                if self.sanction_cache[gtip_code]:
                    sanctioned_codes.append(gtip_code)
                    print(f"   ⛔ Önbellekten yaptırımlı: {gtip_code}")
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
                        print(f"   ⛔ Yaptırımlı kod: {gtip_code}")
                    else:
                        self.sanction_cache[gtip_code] = False
                        print(f"   ✅ Kod temiz: {gtip_code}")
                else:
                    print(f"   ❌ EUR-Lex hatası: {response.status_code}")
                
            except Exception as e:
                print(f"   ❌ EUR-Lex kontrol hatası: {e}")
                continue
        
        return sanctioned_codes

class EnhancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.searcher = EnhancedSearcher(config)
        self.crawler = AdvancedCrawler(config)
        self.eur_lex_checker = QuickEURLexChecker(config)
    
    def enhanced_analyze(self, company, country):
        """Gelişmiş analiz"""
        print(f"🤖 GELİŞMİŞ ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
        
        search_queries = [
            f"{company} {country} export",
            f"{company} {country} business",
            f"{company} {country} HS code"
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries[:2], 1):
            try:
                print(f"\n🔍 Sorgu {i}/2: {query}")
                
                search_results = self.searcher.enhanced_search(query, self.config.MAX_RESULTS)
                
                if not search_results:
                    print(f"   ⚠️ Bu sorgu için sonuç bulunamadı")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    print(f"   📄 Sonuç {j} analiz ediliyor: {result['title'][:50]}...")
                    
                    # Gelişmiş crawl
                    crawl_result = self.crawler.advanced_crawl(result['url'], country)
                    
                    # Eğer sayfaya erişilemediyse, snippet derinlemesine analiz
                    if crawl_result['status_code'] != 200:
                        snippet_analysis = self.crawler.analyze_snippet_deep(result['full_text'], country)
                        if snippet_analysis['country_found'] or snippet_analysis['gtip_codes']:
                            crawl_result['country_found'] = snippet_analysis['country_found']
                            crawl_result['gtip_codes'] = snippet_analysis['gtip_codes']
                            print(f"   🔍 Snippet analizi sonucu: Ülke={snippet_analysis['country_found']}, GTIP={snippet_analysis['gtip_codes']}")
                    
                    # EUR-Lex kontrolü
                    sanctioned_gtips = []
                    if crawl_result['gtip_codes']:
                        print(f"   🔍 EUR-Lex kontrolü yapılıyor...")
                        sanctioned_gtips = self.eur_lex_checker.quick_check_gtip(crawl_result['gtip_codes'])
                    
                    # Güven seviyesi hesapla
                    confidence = self._calculate_confidence(crawl_result, sanctioned_gtips, result['domain'])
                    
                    analysis = self.create_enhanced_analysis_result(
                        company, country, result, crawl_result, sanctioned_gtips, confidence
                    )
                    
                    all_results.append(analysis)
                
                if i < 2:
                    time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Sorgu hatası: {e}")
                continue
        
        return all_results
    
    def _calculate_confidence(self, crawl_result, sanctioned_gtips, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # Domain güveni
        trusted_domains = ['trademo.com', 'eximpedia.app', 'volza.com', 'importyet.com']
        if any(trusted in domain for trusted in trusted_domains):
            confidence += 30
            print(f"   📊 Domain güveni: +30% ({domain})")
        
        # GTIP kodları
        if crawl_result['gtip_codes']:
            confidence += 25
            print(f"   📊 GTIP güveni: +25% ({len(crawl_result['gtip_codes'])} kod)")
        
        # Ülke bağlantısı
        if crawl_result['country_found']:
            confidence += 25
            print(f"   📊 Ülke bağlantısı güveni: +25%")
        
        # Yaptırım tespiti
        if sanctioned_gtips:
            confidence += 20
            print(f"   📊 Yaptırım tespiti güveni: +20% ({len(sanctioned_gtips)} yaptırımlı kod)")
        
        final_confidence = min(confidence, 100)
        print(f"   📊 Toplam güven seviyesi: %{final_confidence}")
        
        return final_confidence
    
    def create_enhanced_analysis_result(self, company, country, search_result, crawl_result, sanctioned_gtips, confidence):
        """Gelişmiş analiz sonucu"""
        
        reasons = []
        if crawl_result['country_found']:
            reasons.append("Ülke bağlantısı tespit edildi")
        if crawl_result['gtip_codes']:
            reasons.append(f"GTIP kodları bulundu: {', '.join(crawl_result['gtip_codes'][:3])}")
        if sanctioned_gtips:
            reasons.append(f"Yaptırımlı GTIP kodları: {', '.join(sanctioned_gtips)}")
        if 'trademo.com' in search_result['domain']:
            reasons.append("Güvenilir ticaret verisi kaynağı")
        
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
            'STATUS_CODE': crawl_result.get('status_code', 'N/A'),
            'KAYNAK_URL': search_result['url'],
            'GÜVEN_SEVİYESİ': f"%{confidence}",
            'NEDENLER': ' | '.join(reasons) if reasons else 'Belirsiz'
        }

def create_detailed_excel_report(results, company, country):
    """Detaylı Excel raporu"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_ticaret_analiz.xlsx"
        
        wb = Workbook()
        
        # 1. Sayfa: Analiz Sonuçları
        ws1 = wb.active
        ws1.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI', 'ULKE_BAGLANTISI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'GÜVEN_SEVİYESİ', 'NEDENLER',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET'
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
            ws1.cell(row=row, column=8, value=str(result.get('GÜVEN_SEVİYESİ', '')))
            ws1.cell(row=row, column=9, value=str(result.get('NEDENLER', '')))
            ws1.cell(row=row, column=10, value=str(result.get('AI_AÇIKLAMA', '')))
            ws1.cell(row=row, column=11, value=str(result.get('AI_TAVSIYE', '')))
            ws1.cell(row=row, column=12, value=str(result.get('BAŞLIK', '')))
            ws1.cell(row=row, column=13, value=str(result.get('URL', '')))
            ws1.cell(row=row, column=14, value=str(result.get('ÖZET', '')))
        
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
        
        # Ortalama Güven Seviyesi
        avg_confidence = sum([int(r.get('GÜVEN_SEVİYESİ', '0%').strip('%')) for r in results if r.get('GÜVEN_SEVİYESİ')]) // max(len(results), 1)
        ws2['A11'] = "ORTALAMA GÜVEN:"
        ws2['B11'] = f"%{avg_confidence}"
        
        # Yapay Zeka Yorumu
        ws2['A13'] = "🤖 YAPAY ZEKA ANALİZ YORUMU:"
        ws2['A13'].font = Font(bold=True)
        
        if high_risk_count > 0:
            yorum = f"⛔ KRİTİK RİSK! {company} şirketinin {country} ile yaptırımlı ürün ticareti tespit edildi. "
            yorum += f"Toplam {high_risk_count} farklı kaynakta yaptırımlı GTIP kodları bulundu. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Acil önlem alınması gerekmektedir."
        elif medium_risk_count > 0:
            yorum = f"🟡 ORTA RİSK! {company} şirketinin {country} ile ticaret bağlantısı bulundu. "
            yorum += f"{medium_risk_count} farklı kaynakta ticaret ilişkisi doğrulandı. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Detaylı inceleme önerilir."
        elif country_connection_count > 0:
            yorum = f"🟢 DÜŞÜK RİSK! {company} şirketinin {country} ile bağlantısı bulundu ancak yaptırım riski tespit edilmedi. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Standart ticaret prosedürleri uygulanabilir."
        else:
            yorum = f"✅ TEMİZ! {company} şirketinin {country} ile ticaret bağlantısı bulunamadı. "
            yorum += f"Ortalama güven seviyesi: %{avg_confidence}. Herhangi bir yaptırım riski tespit edilmedi."
        
        ws2['A14'] = yorum
        
        # Tavsiyeler
        ws2['A16'] = "💡 YAPAY ZEKA TAVSİYELERİ:"
        ws2['A16'].font = Font(bold=True)
        
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
        
        ws2['A17'] = tavsiye
        
        # Kaynaklar
        ws2['A19'] = "🔍 ANALİZ EDİLEN KAYNAKLAR:"
        ws2['A19'].font = Font(bold=True)
        
        for i, result in enumerate(results[:5], 1):
            ws2[f'A{20 + i}'] = f"{i}. {result.get('BAŞLIK', '')}"
            ws2[f'B{20 + i}'] = result.get('URL', '')
            ws2[f'C{20 + i}'] = result.get('GÜVEN_SEVİYESİ', '')
        
        # Stil ayarları
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
        
        ws2.column_dimensions['A'].width = 25
        ws2.column_dimensions['B'].width = 50
        ws2.column_dimensions['C'].width = 15
        
        wb.save(filename)
        print(f"✅ Detaylı Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel rapor oluşturma hatası: {e}")
        return None

def display_results(results, company, country):
    """Sonuçları ekranda göster"""
    print(f"\n{'='*80}")
    print(f"📊 GELİŞMİŞ TİCARET ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YÜKSEK'])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'ORTA'])
    country_connection_count = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    
    print(f"\n📈 ÖZET:")
    print(f"   • Toplam Sonuç: {total_results}")
    print(f"   • Ülke Bağlantısı: {country_connection_count}")
    print(f"   • YÜKSEK Yaptırım Riski: {high_risk_count}")
    print(f"   • ORTA Risk: {medium_risk_count}")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK YAPTIRIM UYARISI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YÜKSEK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:60]}...")
                print(f"      Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
                print(f"      Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', '')}")
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   📋 Özet: {result.get('ÖZET', 'N/A')[:100]}...")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Yaptırım Riski: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        if result.get('YAPTIRIMLI_GTIPLER'):
            print(f"   🚫 Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
        print(f"   📊 Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   📋 Nedenler: {result.get('NEDENLER', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ")
    print("🎯 ÖZELLİK: Gelişmiş Snippet Analizi + Güven Seviyesi")
    print("💡 AVANTAJ: TRADEMO.COM HS Code 870830 ve Country of Export tespiti")
    print("🚀 HEDEF: Kritik ticaret verilerini otomatik tespit etme\n")
    
    # Yapılandırma
    config = Config()
    analyzer = EnhancedTradeAnalyzer(config)
    
    # Manuel giriş
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🚀 GELİŞMİŞ ANALİZ BAŞLATILIYOR: {company} ↔ {country}")
    print("⏳ DuckDuckGo'da gelişmiş arama yapılıyor...")
    print("   Snippet derinlemesine analiz ediliyor...")
    print("   TRADEMO.COM HS Code ve Country of Export taranıyor...")
    print("   Güven seviyesi hesaplanıyor...\n")
    
    start_time = time.time()
    results = analyzer.enhanced_analyze(company, country)
    execution_time = time.time() - start_time
    
    if results:
        # Sonuçları göster
        display_results(results, company, country)
        
        # Excel raporu oluştur
        filename = create_detailed_excel_report(results, company, country)
        
        if filename:
            print(f"\n✅ Excel raporu oluşturuldu: {filename}")
            print(f"⏱️  Toplam çalışma süresi: {execution_time:.2f} saniye")
            
            # Excel açma seçeneği
            try:
                open_excel = input("\n📂 Excel dosyasını şimdi açmak ister misiniz? (e/h): ").strip().lower()
                if open_excel == 'e':
                    if os.name == 'nt':  # Windows
                        os.system(f'start excel "{filename}"')
                    elif os.name == 'posix':  # macOS/Linux
                        os.system(f'open "{filename}"' if sys.platform == 'darwin' else f'xdg-open "{filename}"')
                    print("📂 Excel dosyası açılıyor...")
            except Exception as e:
                print(f"⚠️  Dosya otomatik açılamadı: {e}")
                print(f"📁 Lütfen manuel olarak açın: {filename}")
        else:
            print("❌ Excel raporu oluşturulamadı!")
    else:
        print("❌ Analiz sonucu bulunamadı!")

if __name__ == "__main__":
    main()
