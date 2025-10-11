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

print("🚀 AKILLI TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

class SmartTradeAnalyzer:
    def __init__(self, config):
        self.config = config
    
    def analyze_company(self, company, country):
        """Ana analiz fonksiyonu"""
        print(f"🎯 ANALİZ: {company} ↔ {country}")
        
        queries = self._generate_queries(company, country)
        all_results = []
        
        for i, query in enumerate(queries, 1):
            print(f"🔍 Sorgu {i}/{len(queries)}: {query}")
            
            if i > 1:
                time.sleep(2)
            
            results = self._search_duckduckgo(query)
            
            for result in results:
                analysis = self._analyze_search_result(result, company, country)
                if analysis and self._is_relevant_result(analysis, result['domain']):
                    all_results.append(analysis)
        
        return all_results
    
    def _generate_queries(self, company, country):
        """Arama sorgularını oluştur"""
        return [
            f'"{company}" "{country}" export',
            f'"{company}" "{country}" import',
            f'site:trademo.com "{company}"',
            f'site:eximpedia.app "{company}"',
        ]
    
    def _search_duckduckgo(self, query):
        """DuckDuckGo'da arama"""
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query, 'b': '', 'kl': 'us-en'}
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._parse_results(response.text)
            return []
        except Exception as e:
            print(f"❌ Arama hatası: {e}")
            return []
    
    def _parse_results(self, html):
        """Arama sonuçlarını parse et"""
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
                
                domain = self._extract_domain(url)
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'domain': domain,
                    'full_text': f"{title} {snippet}"
                })
                
                print(f"   📄 Bulundu: {title[:50]}... [{domain}]")
                
            except Exception as e:
                print(f"   ❌ Sonuç hatası: {e}")
                continue
        
        return results
    
    def _analyze_search_result(self, result, company, country):
        """Arama sonucunu analiz et"""
        try:
            combined_text = result['full_text'].lower()
            domain = result['domain']
            
            # Ülke kontrolü
            country_found = self._check_country(combined_text, country, domain)
            
            # GTIP kontrolü
            gtip_codes = self._extract_gtip_codes(combined_text, domain)
            
            # Güven seviyesi
            confidence = self._calculate_confidence(country_found, gtip_codes, domain)
            
            # Risk analizi
            risk_data = self._assess_risk(country_found, gtip_codes, company, country, confidence)
            
            return {
                **risk_data,
                'BAŞLIK': result['title'],
                'URL': result['url'],
                'ÖZET': result['snippet'],
                'GÜVEN_SEVİYESİ': f"%{confidence}",
                'KAYNAK': domain
            }
            
        except Exception as e:
            print(f"   ❌ Analiz hatası: {e}")
            return None
    
    def _check_country(self, text_lower, target_country, domain):
        """Ülke bağlantısını kontrol et"""
        # Rusya için özel pattern'ler
        russia_patterns = [
            'russia', 'rusya', 'russian', 'rusian', 'rus'
        ]
        
        # Ticaret terimleri
        trade_terms = ['export', 'import', 'destination', 'country of export', 'supplier']
        
        # Eximpedia için Destination Russia kontrolü
        if 'eximpedia.app' in domain:
            if 'destination russia' in text_lower or 'export russia' in text_lower:
                print("   ✅ Eximpedia: Destination Russia tespit edildi")
                return True
        
        # Trademo için Country of Export kontrolü
        if 'trademo.com' in domain:
            if 'country of export russia' in text_lower:
                print("   ✅ Trademo: Country of Export Russia tespit edildi")
                return True
        
        # Genel kontrol
        for country_pattern in russia_patterns:
            if country_pattern in text_lower:
                # Ticaret bağlantısı var mı?
                for term in trade_terms:
                    if term in text_lower:
                        print(f"   ✅ Ülke-trade bağlantısı: {country_pattern} + {term}")
                        return True
                print(f"   ✅ Ülke bulundu: {country_pattern}")
                return True
        
        return False
    
    def _extract_gtip_codes(self, text, domain):
        """GTIP kodlarını çıkar"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\b\d{6}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
        ]
        
        codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    codes.add(code[:4])
                    print(f"   🔍 GTIP bulundu: {code[:4]}")
        
        # Otomatik 8708 ekleme
        if any(site in domain for site in ['trademo.com', 'eximpedia.app']):
            if '8708' in text or '870830' in text:
                codes.add('8708')
                print("   🔍 Otomatik 8708 eklendi")
        
        return list(codes)
    
    def _calculate_confidence(self, country_found, gtip_codes, domain):
        """Güven seviyesi hesapla"""
        confidence = 0
        
        # Domain güveni
        if any(trusted in domain for trusted in ['trademo.com', 'eximpedia.app']):
            confidence += 40
        elif 'volza.com' in domain:
            confidence += 30
        
        # Ülke bağlantısı
        if country_found:
            confidence += 30
        
        # GTIP kodları
        if gtip_codes:
            confidence += 30
        
        return min(confidence, 100)
    
    def _assess_risk(self, country_found, gtip_codes, company, country, confidence):
        """Risk değerlendirmesi"""
        if country_found and gtip_codes:
            status = "RISK_VAR"
            explanation = f"🟡 RİSK: {company} şirketinin {country} ile ticaret bağlantısı bulundu"
            advice = f"GTIP kodları: {', '.join(gtip_codes)} - Detaylı inceleme önerilir"
            risk_level = "ORTA"
        elif country_found:
            status = "İLİŞKİ_VAR"
            explanation = f"🟢 İLİŞKİ: {company} şirketinin {country} ile bağlantısı var"
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
            'TESPIT_EDILEN_GTIPLER': ', '.join(gtip_codes),
            'ULKE_BAGLANTISI': 'EVET' if country_found else 'HAYIR',
        }
    
    def _is_relevant_result(self, analysis, domain):
        """Sonucun alakalı olup olmadığını kontrol et"""
        # Sadece güvenilir domain'ler veya ülke bağlantısı olanlar
        trusted_domains = ['trademo.com', 'eximpedia.app', 'volza.com']
        
        if any(trusted in domain for trusted in trusted_domains):
            return True
        
        if analysis['ULKE_BAGLANTISI'] == 'EVET':
            return True
        
        return False
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

def display_results(results, company, country):
    """Sonuçları göster"""
    print(f"\n{'='*80}")
    print(f"📊 ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Sonuç bulunamadı!")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   ⚠️  Risk: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔗 Ülke Bağlantısı: {result.get('ULKE_BAGLANTISI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        print(f"   📊 Güven: {result.get('GÜVEN_SEVİYESİ', 'N/A')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   🌐 Kaynak: {result.get('KAYNAK', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("🚀 AKILLI TİCARET ANALİZ SİSTEMİ")
    print("🎯 HEDEF: Gerçek ticaret bağlantılarını tespit etme")
    print("💡 ÖZELLİK: Eximpedia Destination Russia ve Trademo Country of Export tespiti\n")
    
    config = Config()
    analyzer = SmartTradeAnalyzer(config)
    
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 ANALİZ BAŞLATILIYOR...")
    start_time = time.time()
    
    results = analyzer.analyze_company(company, country)
    
    execution_time = time.time() - start_time
    
    display_results(results, company, country)
    
    print(f"\n⏱️  Toplam süre: {execution_time:.2f} saniye")
    print(f"📊 Toplam sonuç: {len(results)}")

if __name__ == "__main__":
    main()
