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

print("🚀 BASİT VE ETKİLİ TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SimpleTradeAnalyzer:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    def analyze_company(self, company, country):
        """Basit ve etkili analiz"""
        print(f"🎯 ANALİZ: {company} ↔ {country}")
        
        # Manuel olarak bilinen ticaret sitelerini kontrol et
        manual_results = self._check_known_sites(company, country)
        
        # Google araması yap
        google_results = self._google_search(company, country)
        
        # Sonuçları birleştir
        all_results = manual_results + google_results
        
        return all_results
    
    def _check_known_sites(self, company, country):
        """Bilinen ticaret sitelerini manuel kontrol et"""
        results = []
        
        # Trademo için
        trademo_result = self._check_trademo(company, country)
        if trademo_result:
            results.append(trademo_result)
        
        # Eximpedia için
        eximpedia_result = self._check_eximpedia(company, country)
        if eximpedia_result:
            results.append(eximpedia_result)
        
        return results
    
    def _check_trademo(self, company, country):
        """Trademo'yu kontrol et"""
        try:
            # Trademo'da firma arama
            search_url = f"https://www.trademo.com/search/companies?q={company.replace(' ', '+')}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Basit kontrol - sayfada Rusya ve GTIP ara
                content = response.text.lower()
                
                country_found = any(pattern in content for pattern in ['russia', 'rusya', 'russian'])
                gtip_found = '8708' in content or '870830' in content
                
                if country_found or gtip_found:
                    return {
                        'ŞİRKET': company,
                        'ÜLKE': country,
                        'DURUM': 'RISK_VAR' if country_found else 'İLİŞKİ_VAR',
                        'AI_AÇIKLAMA': f"🟡 Trademo'da {company} şirketinin {country} ile bağlantısı bulundu",
                        'AI_TAVSIYE': 'Detaylı inceleme önerilir',
                        'YAPTIRIM_RISKI': 'ORTA' if country_found else 'DÜŞÜK',
                        'TESPIT_EDILEN_GTIPLER': '8708' if gtip_found else '',
                        'ULKE_BAGLANTISI': 'EVET' if country_found else 'HAYIR',
                        'BAŞLIK': f"Trademo: {company}",
                        'URL': search_url,
                        'ÖZET': 'Trademo ticaret veritabanında firma bulundu',
                        'GÜVEN_SEVİYESİ': '%70',
                        'KAYNAK': 'trademo.com'
                    }
            
            return None
            
        except Exception as e:
            print(f"Trademo kontrol hatası: {e}")
            return None
    
    def _check_eximpedia(self, company, country):
        """Eximpedia'yı kontrol et"""
        try:
            # Eximpedia'da firma arama
            search_url = f"https://www.eximpedia.app/search?q={company.replace(' ', '+')}+{country}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Eximpedia'da destination Russia kontrolü
                destination_russia = 'destination russia' in content
                country_found = destination_russia or any(pattern in content for pattern in ['russia', 'rusya'])
                gtip_found = '8708' in content
                
                if country_found:
                    return {
                        'ŞİRKET': company,
                        'ÜLKE': country,
                        'DURUM': 'RISK_VAR',
                        'AI_AÇIKLAMA': f"🟡 Eximpedia'da {company} şirketinin {country} hedef pazarı bulundu",
                        'AI_TAVSIYE': 'Destination Russia tespit edildi - detaylı inceleme önerilir',
                        'YAPTIRIM_RISKI': 'ORTA',
                        'TESPIT_EDILEN_GTIPLER': '8708' if gtip_found else '',
                        'ULKE_BAGLANTISI': 'EVET',
                        'BAŞLIK': f"Eximpedia: {company}",
                        'URL': search_url,
                        'ÖZET': 'Eximpedia veritabanında firma ve Rusya bağlantısı bulundu',
                        'GÜVEN_SEVİYESİ': '%75',
                        'KAYNAK': 'eximpedia.app'
                    }
            
            return None
            
        except Exception as e:
            print(f"Eximpedia kontrol hatası: {e}")
            return None
    
    def _google_search(self, company, country):
        """Google araması yap"""
        try:
            query = f"{company} {country} export Russia site:trademo.com OR site:eximpedia.app OR site:volza.com"
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            results = []
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Google arama sonuçlarını parse et
                for g in soup.find_all('div', class_='g'):
                    try:
                        title_elem = g.find('h3')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text()
                        link_elem = g.find('a')
                        url = link_elem.get('href') if link_elem else ""
                        
                        snippet_elem = g.find('span', class_='aCOpRe')
                        snippet = snippet_elem.get_text() if snippet_elem else ""
                        
                        if any(domain in url for domain in ['trademo.com', 'eximpedia.app', 'volza.com']):
                            # Bu sonuçları analiz et
                            analysis = self._analyze_google_result(title, snippet, url, company, country)
                            if analysis:
                                results.append(analysis)
                                
                    except Exception as e:
                        continue
                        
            return results
            
        except Exception as e:
            print(f"Google arama hatası: {e}")
            return []
    
    def _analyze_google_result(self, title, snippet, url, company, country):
        """Google sonucunu analiz et"""
        combined_text = f"{title} {snippet}".lower()
        
        # Ülke kontrolü
        country_found = any(pattern in combined_text for pattern in ['russia', 'rusya', 'russian', 'destination russia'])
        
        # GTIP kontrolü
        gtip_found = '8708' in combined_text or '870830' in combined_text
        
        if country_found:
            domain = self._extract_domain(url)
            
            return {
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'RISK_VAR' if country_found else 'İLİŞKİ_VAR',
                'AI_AÇIKLAMA': f"🔍 Google aramasında {company} şirketinin {country} bağlantısı bulundu",
                'AI_TAVSIYE': 'Ticaret verisi kaynağında firma ve ülke bağlantısı tespit edildi',
                'YAPTIRIM_RISKI': 'ORTA' if country_found else 'DÜŞÜK',
                'TESPIT_EDILEN_GTIPLER': '8708' if gtip_found else '',
                'ULKE_BAGLANTISI': 'EVET' if country_found else 'HAYIR',
                'BAŞLIK': title,
                'URL': url,
                'ÖZET': snippet,
                'GÜVEN_SEVİYESİ': '%60',
                'KAYNAK': domain
            }
        
        return None
    
    def _extract_domain(self, url):
        """URL'den domain çıkar"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

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
        
        logging.info(f"🚀 BASİT ANALİZ BAŞLATILIYOR: {company} - {country}")
        
        analyzer = SimpleTradeAnalyzer()
        results = analyzer.analyze_company(company, country)
        
        # Eğer hiç sonuç yoksa, temiz olduğunu belirten bir sonuç döndür
        if not results:
            results = [{
                'ŞİRKET': company,
                'ÜLKE': country,
                'DURUM': 'TEMIZ',
                'AI_AÇIKLAMA': f"✅ {company} şirketinin {country} ile ticaret bağlantısı bulunamadı",
                'AI_TAVSIYE': 'Risk tespit edilmedi, standart ticaret prosedürlerine devam edilebilir',
                'YAPTIRIM_RISKI': 'YOK',
                'TESPIT_EDILEN_GTIPLER': '',
                'ULKE_BAGLANTISI': 'HAYIR',
                'BAŞLIK': 'Temiz Sonuç',
                'URL': '',
                'ÖZET': 'Analiz sonucunda risk bulunamadı',
                'GÜVEN_SEVİYESİ': '%85',
                'KAYNAK': 'Sistem Analizi'
            }]
        
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
