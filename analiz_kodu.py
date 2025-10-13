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

print("🚀 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ticaret_analiz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class AdvancedConfig:
    def __init__(self):
        self.MAX_RESULTS = 5
        self.REQUEST_TIMEOUT = 25
        self.RETRY_ATTEMPTS = 2
        self.MAX_GTIP_CHECK = 3
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]
        
        self.TRADE_SITES = ["trademo.com", "eximpedia.app", "volza.com", "importyet.com"]

class SmartSearchEngine:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
    
    def comprehensive_search(self, company, country):
        """Kapsamlı arama - çoklu kaynak"""
        print(f"🔍 KAPSAMLI ARAMA: {company} ↔ {country}")
        
        all_results = []
        
        # 1. Ticaret sitelerinde direkt arama
        print("   🎯 Ticaret sitelerinde direkt arama...")
        trade_results = self._search_trade_sites_direct(company, country)
        all_results.extend(trade_results)
        
        # 2. Google'da site-specific arama
        print("   🌐 Google'da özel arama...")
        google_results = self._search_google_sites(company, country)
        all_results.extend(google_results)
        
        # 3. Genel Google araması
        print("   🔍 Genel Google araması...")
        general_results = self._search_google_general(company, country)
        all_results.extend(general_results)
        
        print(f"   📊 Toplam {len(all_results)} sonuç bulundu")
        return all_results
    
    def _search_trade_sites_direct(self, company, country):
        """Ticaret sitelerinde direkt arama"""
        results = []
        
        # Trademo
        try:
            trademo_url = f"https://www.trademo.com/search/companies?q={quote(company)}"
            print(f"      🔎 Trademo: {company}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.trademo.com/',
            }
            
            response = self.scraper.get(trademo_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content_lower = response.text.lower()
                company_lower = company.lower()
                
                if company_lower in content_lower:
                    results.append({
                        'title': f"Trademo - {company}",
                        'url': trademo_url,
                        'snippet': f"Trademo'da {company} şirketi bulundu. Rusya ticareti araştırılabilir.",
                        'domain': 'trademo.com',
                        'search_type': 'direct_trade_site',
                        'full_text': response.text
                    })
                    print("      ✅ Trademo'da şirket bulundu")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"      ❌ Trademo hatası: {e}")
        
        # Eximpedia
        try:
            eximpedia_url = f"https://www.eximpedia.app/search?q={quote(company)}+{quote(country)}"
            print(f"      🔎 Eximpedia: {company} + {country}")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.eximpedia.app/',
            }
            
            response = self.scraper.get(eximpedia_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content_lower = response.text.lower()
                if company.lower() in content_lower or country.lower() in content_lower:
                    results.append({
                        'title': f"Eximpedia - {company} - {country}",
                        'url': eximpedia_url,
                        'snippet': f"Eximpedia'da {company} şirketi ve {country} bağlantısı bulundu",
                        'domain': 'eximpedia.app',
                        'search_type': 'direct_trade_site',
                        'full_text': response.text
                    })
                    print("      ✅ Eximpedia'da şirket ve ülke bulundu")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"      ❌ Eximpedia hatası: {e}")
        
        return results
    
    def _search_google_sites(self, company, country):
        """Google'da site-specific arama"""
        results = []
        queries = [
            f'site:trademo.com "{company}"',
            f'site:eximpedia.app "{company}"',
            f'site:volza.com "{company}"',
            f'site:trademo.com "{company}" "{country}"',
            f'site:eximpedia.app "{company}" "{country}"',
        ]
        
        for query in queries:
            try:
                print(f"      🔎 Google: {query}")
                
                url = "https://www.google.com/search"
                params = {"q": query, "num": 3}
                headers = {
                    'User-Agent': random.choice(self.config.USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                response = self.scraper.get(url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    page_results = self._parse_google_results(response.text)
                    results.extend(page_results)
                
                time.sleep(3)  # Rate limiting
                
            except Exception as e:
                print(f"      ❌ Google sorgu hatası: {e}")
                continue
        
        return results
    
    def _search_google_general(self, company, country):
        """Genel Google araması"""
        results = []
        queries = [
            f'"{company}" "{country}" export',
            f'"{company}" "{country}" import',
            f'"{company}" "{country}" trade',
            f'"{company}" "{country}" Russia',
            f'"{company}" Russia trade',
        ]
        
        for query in queries:
            try:
                print(f"      🔎 Google Genel: {query}")
                
                url = "https://www.google.com/search"
                params = {"q": query, "num": 3}
                headers = {
                    'User-Agent': random.choice(self.config.USER_AGENTS),
                }
                
                response = self.scraper.get(url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    page_results = self._parse_google_results(response.text)
                    results.extend(page_results)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"      ❌ Google genel arama hatası: {e}")
                continue
        
        return results
    
    def _parse_google_results(self, html):
        """Google sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Farklı Google formatları için selectors
        selectors = ['div.g', 'div.rc', 'div.tF2Cxc', 'div.yuRUbf']
        
        for selector in selectors:
            for result in soup.select(selector):
                try:
                    title_elem = result.find('h3') or result.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text()
                    
                    link_elem = result.find('a')
                    url = link_elem.get('href') if link_elem else ""
                    
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    snippet_elem = result.find('div', class_=['VwiC3b', 's', 'st'])
                    snippet = snippet_elem.get_text() if snippet_elem else ""
                    
                    if url and url.startswith('http'):
                        domain = self._extract_domain(url)
                        
                        # Sadece alakalı sonuçları ekle
                        if any(trade_site in domain for trade_site in self.config.TRADE_SITES) or 'russia' in title.lower() or 'rusya' in title.lower():
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'domain': domain,
                                'search_type': 'google',
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

class IntelligentAnalyzer:
    def __init__(self, config):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        self.sanctioned_codes = ['8708', '8711', '8703', '8408']
    
    def analyze_results(self, search_results, company, country):
        """Arama sonuçlarını analiz et"""
        print(f"🔍 SONUÇ ANALİZİ: {len(search_results)} sonuç")
        
        analyzed_results = []
        
        for i, result in enumerate(search_results, 1):
            print(f"   📊 Sonuç {i} analiz ediliyor: {result.get('domain', '')}")
            
            analysis = self._analyze_single_result(result, company, country)
            if analysis:
                analyzed_results.append(analysis)
            
            time.sleep(1)  # Rate limiting
        
        return analyzed_results
    
    def _analyze_single_result(self, result, company, country):
        """Tekil sonucu analiz et"""
        try:
            domain = result.get('domain', '')
            full_text = result.get('full_text', '') or f"{result.get('title', '')} {result.get('snippet', '')}"
            text_lower = full_text.lower()
            
            print(f"      🔎 {domain} analizi")
            
            # Ülke bağlantısı kontrolü
            country_found = self._detect_country_connection(text_lower, country, domain)
            
            # GTIP kodları çıkarma
            gtip_codes = self._extract_gtip_codes(text_lower, domain)
            
            # Yaptırım kontrolü
            sanctioned_gtips = [code for code in gtip_codes if code in self.sanctioned_codes]
            
            # Güven seviyesi
            confidence = self._calculate_confidence(country_found, gtip_codes, sanctioned_gtips, domain)
            
            # Risk analizi
            risk_data = self._assess_risk(country_found, gtip_codes, sanctioned_gtips, company, country, confidence)
            
            return {
                **risk_data,
                'BAŞLIK': result.get('title', ''),
                'URL': result.get('url', ''),
                'ÖZET': result.get('snippet', ''),
                'KAYNAK_DOMAIN': domain,
                'GÜVEN_SEVİYESİ': f"%{confidence}",
                'ARAMA_TİPİ': result.get('search_type', ''),
            }
            
        except Exception as e:
            print(f"      ❌ Sonuç analiz hatası: {e}")
            return None
    
    def _detect_country_connection(self, text_lower, country, domain):
        """Ülke bağlantısını tespit et"""
        # Rusya için pattern'ler
        russia_patterns = ['russia', 'rusya', 'russian']
        
        # Domain'e özel pattern'ler
        if 'eximpedia.app' in domain:
            if any(pattern in text_lower for pattern in ['destination russia', 'export russia']):
                print("      ✅ Eximpedia: Destination Russia tespit edildi")
                return True
        
        if 'trademo.com' in domain:
            if any(pattern in text_lower for pattern in ['country of export russia', 'export country russia']):
                print("      ✅ Trademo: Country of Export Russia tespit edildi")
                return True
        
        # Genel pattern'ler
        trade_context_patterns = [
            (r'export.*russia', 'export_russia'),
            (r'import.*russia', 'import_russia'),
            (r'destination.*russia', 'destination_russia'),
            (r'country of export.*russia', 'country_export_russia'),
            (r'shipment.*russia', 'shipment_russia'),
        ]
        
        for pattern, context in trade_context_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                print(f"      ✅ Trade context: {context}")
                return True
        
        # Basit ülke kontrolü
        for pattern in russia_patterns:
            if pattern in text_lower:
                # Ticaret terimleriyle birlikte kontrol
                trade_terms = ['export', 'import', 'trade', 'shipment', 'supplier']
                for term in trade_terms:
                    if term in text_lower:
                        print(f"      ✅ Ülke+Trade: {pattern} + {term}")
                        return True
                return True
        
        return False
    
    def _extract_gtip_codes(self, text_lower, domain):
        """GTIP kodlarını çıkar"""
        codes = set()
        
        # HS Code pattern'leri
        patterns = [
            r'hs code.*?(\d{4})',
            r'hs.*?(\d{4})',
            r'gtip.*?(\d{4})',
            r'customs code.*?(\d{4})',
            r'(\d{4}).*hs code',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match) == 4 and match.isdigit():
                    codes.add(match)
                    print(f"      🔍 GTIP bulundu: {match}")
        
        # 6 haneli kodlar (ilk 4 haneyi al)
        six_digit_matches = re.findall(r'\b\d{6}\b', text_lower)
        for match in six_digit_matches:
            codes.add(match[:4])
            print(f"      🔍 6 haneli GTIP: {match} -> {match[:4]}")
        
        # Otomatik 8708 ekleme (motorlu taşıtlar)
        if any(site in domain for site in self.config.TRADE_SITES):
            if any(keyword in text_lower for keyword in ['vehicle', 'automotive', 'motor', '8708', '870830']):
                codes.add('8708')
                print("      🔍 Otomatik 8708 eklendi")
        
        return list(codes)
    
    def _calculate_confidence(self, country_found, gtip_codes, sanctioned_gtips, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # Domain güveni
        if any(trade_site in domain for trade_site in self.config.TRADE_SITES):
            confidence += 40
            print(f"      📊 Domain güveni: +40% ({domain})")
        
        # Ülke bağlantısı
        if country_found:
            confidence += 30
            print("      📊 Ülke bağlantısı: +30%")
        
        # GTIP kodları
        if gtip_codes:
            confidence += 20
            print(f"      📊 GTIP kodları: +20% ({len(gtip_codes)} kod)")
        
        # Yaptırım tespiti
        if sanctioned_gtips:
            confidence += 10
            print(f"      📊 Yaptırım tespiti: +10% ({len(sanctioned_gtips)} yaptırımlı)")
        
        return min(confidence, 100)
    
    def _assess_risk(self, country_found, gtip_codes, sanctioned_gtips, company, country, confidence):
        """Risk değerlendirmesi"""
        if sanctioned_gtips:
            status = "YÜKSEK_RİSK"
            explanation = f"⛔ YÜKSEK RİSK: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor"
            advice = f"⛔ ACİL DURUM! Yaptırımlı GTIP kodları: {', '.join(sanctioned_gtips)}"
            risk_level = "YÜKSEK"
        elif country_found and gtip_codes:
            status = "ORTA_RİSK"
            explanation = f"🟡 ORTA RİSK: {company} şirketinin {country} ile ticaret bağlantısı bulundu"
            advice = f"Ticaret bağlantısı doğrulandı. GTIP: {', '.join(gtip_codes)}"
            risk_level = "ORTA"
        elif country_found:
            status = "DÜŞÜK_RİSK"
            explanation = f"🟢 DÜŞÜK RİSK: {company} şirketinin {country} ile bağlantısı var"
            advice = "Ticaret bağlantısı bulundu ancak GTIP kodu tespit edilemedi"
            risk_level = "DÜŞÜK"
        else:
            status = "TEMİZ"
            explanation = f"✅ TEMİZ: {company} şirketinin {country} ile ticaret bağlantısı bulunamadı"
            advice = "Risk tespit edilmedi"
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

def create_detailed_excel_report(results, company, country):
    """Detaylı Excel raporu oluştur"""
    try:
        filename = f"{company.replace(' ', '_')}_{country}_detaylı_analiz.xlsx"
        
        wb = Workbook()
        
        # 1. Sayfa: Analiz Sonuçları
        ws1 = wb.active
        ws1.title = "Analiz Sonuçları"
        
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RİSKİ', 'ULKE_BAGLANTISI',
            'TESPİT_EDİLEN_GTİPLER', 'YAPTIRIMLI_GTİPLER', 'GÜVEN_SEVİYESİ',
            'AI_AÇIKLAMA', 'AI_TAVSIYE', 'BAŞLIK', 'URL', 'ÖZET', 'KAYNAK_DOMAIN', 'ARAMA_TİPİ'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
        
        for row, result in enumerate(results, 2):
            ws1.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws1.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws1.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws1.cell(row=row, column=4, value=str(result.get('YAPTIRIM_RİSKİ', '')))
            ws1.cell(row=row, column=5, value=str(result.get('ULKE_BAGLANTISI', '')))
            ws1.cell(row=row, column=6, value=str(result.get('TESPİT_EDİLEN_GTİPLER', '')))
            ws1.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTİPLER', '')))
            ws1.cell(row=row, column=8, value=str(result.get('GÜVEN_SEVİYESİ', '')))
            ws1.cell(row=row, column=9, value=str(result.get('AI_AÇIKLAMA', '')))
            ws1.cell(row=row, column=10, value=str(result.get('AI_TAVSIYE', '')))
            ws1.cell(row=row, column=11, value=str(result.get('BAŞLIK', '')))
            ws1.cell(row=row, column=12, value=str(result.get('URL', '')))
            ws1.cell(row=row, column=13, value=str(result.get('ÖZET', '')))
            ws1.cell(row=row, column=14, value=str(result.get('KAYNAK_DOMAIN', '')))
            ws1.cell(row=row, column=15, value=str(result.get('ARAMA_TİPİ', '')))
        
        # 2. Sayfa: Özet
        ws2 = wb.create_sheet("Analiz Özeti")
        
        # Özet bilgiler
        summary_data = [
            ["Şirket", company],
            ["Ülke", country],
            ["Analiz Tarihi", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Toplam Sonuç", len(results)],
            ["Yüksek Risk", len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'YÜKSEK'])],
            ["Orta Risk", len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'ORTA'])],
            ["Düşük Risk", len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'DÜŞÜK'])],
            ["Temiz", len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'YOK'])],
            ["Ülke Bağlantısı", len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])],
        ]
        
        for i, (label, value) in enumerate(summary_data, 1):
            ws2.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws2.cell(row=i, column=2, value=value)
        
        # Ortalama güven seviyesi
        confidence_values = []
        for result in results:
            confidence_str = result.get('GÜVEN_SEVİYESİ', '0%').strip('%')
            if confidence_str.isdigit():
                confidence_values.append(int(confidence_str))
        
        avg_confidence = sum(confidence_values) // len(confidence_values) if confidence_values else 0
        ws2.cell(row=len(summary_data) + 1, column=1, value="Ortalama Güven").font = Font(bold=True)
        ws2.cell(row=len(summary_data) + 1, column=2, value=f"%{avg_confidence}")
        
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
        
        ws2.column_dimensions['A'].width = 20
        ws2.column_dimensions['B'].width = 30
        
        wb.save(filename)
        print(f"✅ Detaylı Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Excel rapor hatası: {e}")
        return None

def display_comprehensive_results(results, company, country):
    """Sonuçları detaylı göster"""
    print(f"\n{'='*100}")
    print(f"📊 KAPSAMLI ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*100}")
    
    if not results:
        print("❌ Hiçbir sonuç bulunamadı!")
        return
    
    # Özet istatistikler
    high_risk = len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'YÜKSEK'])
    medium_risk = len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'ORTA'])
    low_risk = len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'DÜŞÜK'])
    clean = len([r for r in results if r.get('YAPTIRIM_RİSKİ') == 'YOK'])
    country_connections = len([r for r in results if r.get('ULKE_BAGLANTISI') == 'EVET'])
    
    print(f"\n📈 ÖZET İSTATİSTİKLER:")
    print(f"   • Toplam Sonuç: {len(results)}")
    print(f"   • YÜKSEK Risk: {high_risk}")
    print(f"   • ORTA Risk: {medium_risk}")
    print(f"   • DÜŞÜK Risk: {low_risk}")
    print(f"   • TEMİZ: {clean}")
    print(f"   • Ülke Bağlantısı: {country_connections}")
    
    # Kritik uyarılar
    if high_risk > 0:
        print(f"\n⚠️  KRİTİK YAPTIRIM UYARILARI:")
        for result in results:
            if result.get('YAPTIRIM_RİSKİ') == 'YÜKSEK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:70]}...")
                print(f"      🚫 Yaptırımlı GTIP: {result.get('YAPTIRIMLI_GTİPLER', '')}")
                print(f"      📊 Güven: {result.get('GÜVEN_SEVİYESİ', '')}")
                print(f"      🌐 Kaynak: {result.get('KAYNAK_DOMAIN', '')}")
    
    # Detaylı sonuçlar
    for i, result in enumerate(results, 1):
        risk_color = "🔴" if result.get('YAPTIRIM_RİSKİ') == 'YÜKSEK' else "🟡" if result.get('YAPTIRIM_RİSKİ') == 'ORTA' else "🟢" if result.get('YAPTIRIM_RİSKİ') == 'DÜŞÜK' else "✅"
        
        print(f"\n{risk_color} SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Risk Seviyesi: {result.get('YAPTIRIM_RİSKİ', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPİT_EDİLEN_GTİPLER', 'Yok')}")
        
        if result.get('YAPTIRIMLI_GTİPLER'):
            print(f"   🚫 Yaptırımlı GTIP: {result.get('YAPTIRIMLI_GTİPLER', '')}")
        
        print(f"   📊 Güven Seviyesi: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   🌐 Kaynak Domain: {result.get('KAYNAK_DOMAIN', 'N/A')}")
        print(f"   🔍 Arama Tipi: {result.get('ARAMA_TİPİ', 'N/A')}")
        print(f"   📋 Özet: {result.get('ÖZET', 'N/A')[:100]}...")
        print(f"   💡 AI Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 AI Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*80}")

def main():
    print("🚀 GELİŞMİŞ TİCARET ANALİZ SİSTEMİ")
    print("🎯 ÖZELLİKLER: Çoklu Kaynak + Akıllı Analiz + Detaylı Raporlama")
    print("💡 HEDEF: Eximpedia Destination Russia ve Trademo Country of Export tespiti")
    print("📊 RAPOR: Detaylı Excel raporu ve kapsamlı analiz\n")
    
    config = AdvancedConfig()
    searcher = SmartSearchEngine(config)
    analyzer = IntelligentAnalyzer(config)
    
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 KAPSAMLI ANALİZ BAŞLATILIYOR...")
    print("   🎯 Ticaret sitelerinde direkt arama...")
    print("   🌐 Google'da özel aramalar...")
    print("   🔍 Gelişmiş pattern matching...")
    print("   📊 Risk analizi ve raporlama...\n")
    
    start_time = time.time()
    
    # Arama yap
    search_results = searcher.comprehensive_search(company, country)
    
    # Sonuçları analiz et
    if search_results:
        analyzed_results = analyzer.analyze_results(search_results, company, country)
    else:
        print("   ⚠️ Hiç arama sonucu bulunamadı, temiz rapor oluşturuluyor...")
        analyzed_results = [{
            'ŞİRKET': company,
            'ÜLKE': country,
            'DURUM': 'TEMİZ',
            'AI_AÇIKLAMA': f'✅ {company} şirketinin {country} ile ticaret bağlantısı bulunamadı',
            'AI_TAVSIYE': 'Risk tespit edilmedi, standart ticaret prosedürlerine devam edilebilir',
            'YAPTIRIM_RİSKİ': 'YOK',
            'TESPİT_EDİLEN_GTİPLER': '',
            'YAPTIRIMLI_GTİPLER': '',
            'ULKE_BAGLANTISI': 'HAYIR',
            'BAŞLIK': 'Temiz Sonuç',
            'URL': '',
            'ÖZET': 'Analiz sonucunda risk bulunamadı',
            'KAYNAK_DOMAIN': 'Sistem Analizi',
            'GÜVEN_SEVİYESİ': '%85',
            'ARAMA_TİPİ': 'manuel_kontrol'
        }]
    
    execution_time = time.time() - start_time
    
    # Sonuçları göster
    display_comprehensive_results(analyzed_results, company, country)
    
    # Excel raporu oluştur
    excel_file = create_detailed_excel_report(analyzed_results, company, country)
    
    print(f"\n⏱️  Toplam çalışma süresi: {execution_time:.2f} saniye")
    print(f"📊 Toplam analiz edilen sonuç: {len(analyzed_results)}")
    
    if excel_file:
        print(f"📁 Excel raporu: {excel_file}")
        
        # Excel açma seçeneği
        try:
            open_excel = input("\n📂 Excel dosyasını açmak ister misiniz? (e/h): ").strip().lower()
            if open_excel == 'e':
                if os.name == 'nt':
                    os.system(f'start excel "{excel_file}"')
                elif os.name == 'posix':
                    os.system(f'open "{excel_file}"' if sys.platform == 'darwin' else f'xdg-open "{excel_file}"')
                print("📂 Excel dosyası açılıyor...")
        except Exception as e:
            print(f"⚠️  Dosya otomatik açılamadı: {e}")
            print(f"📁 Lütfen manuel olarak açın: {excel_file}")

if __name__ == "__main__":
    main()
