import requests
from bs4 import BeautifulSoup
import time
import random
import re

print("🚀 BASİT TİCARET ANALİZ SİSTEMİ BAŞLATILIYOR...")

class SimpleAnalyzer:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    def analyze(self, company, country):
        """Basit analiz"""
        print(f"🎯 ANALİZ: {company} ↔ {country}")
        
        results = []
        
        # 1. Trademo kontrolü
        print("🔍 Trademo kontrol ediliyor...")
        trademo_result = self._check_trademo(company, country)
        if trademo_result:
            results.append(trademo_result)
        
        # 2. Eximpedia kontrolü
        print("🔍 Eximpedia kontrol ediliyor...")
        eximpedia_result = self._check_eximpedia(company, country)
        if eximpedia_result:
            results.append(eximpedia_result)
        
        # 3. Google araması
        print("🔍 Google'da aranıyor...")
        google_results = self._google_search(company, country)
        results.extend(google_results)
        
        return results
    
    def _check_trademo(self, company, country):
        """Trademo'yu kontrol et"""
        try:
            url = f"https://www.trademo.com/search/companies?q={company.replace(' ', '+')}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                country_found = any(word in content for word in ['russia', 'rusya', 'russian'])
                gtip_found = '8708' in content
                
                if country_found:
                    return {
                        'site': 'Trademo',
                        'url': url,
                        'ülke_bağlantısı': 'EVET' if country_found else 'HAYIR',
                        'gtip_kodları': '8708' if gtip_found else 'Yok',
                        'açıklama': f"Trademo'da {company} ve Rusya bağlantısı bulundu"
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Trademo hatası: {e}")
            return None
    
    def _check_eximpedia(self, company, country):
        """Eximpedia'yı kontrol et"""
        try:
            url = f"https://www.eximpedia.app/search?q={company.replace(' ', '+')}+{country}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                destination_russia = 'destination russia' in content
                country_found = destination_russia or any(word in content for word in ['russia', 'rusya'])
                
                if country_found:
                    return {
                        'site': 'Eximpedia',
                        'url': url,
                        'ülke_bağlantısı': 'EVET',
                        'gtip_kodları': '8708' if '8708' in content else 'Yok',
                        'açıklama': f"Eximpedia'da Destination Russia bulundu"
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Eximpedia hatası: {e}")
            return None
    
    def _google_search(self, company, country):
        """Google'da ara"""
        try:
            query = f"{company} {country} export Russia"
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = requests.get(url, headers=headers, timeout=10)
            results = []
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Basit sonuç çıkarma
                for i, g in enumerate(soup.find_all('div', class_='g')[:3]):
                    try:
                        title_elem = g.find('h3')
                        title = title_elem.get_text() if title_elem else f"Sonuç {i+1}"
                        
                        link_elem = g.find('a')
                        link = link_elem.get('href') if link_elem else ""
                        
                        results.append({
                            'site': 'Google',
                            'url': link,
                            'ülke_bağlantısı': 'EVET' if any(word in title.lower() for word in ['russia', 'rusya']) else 'BELİRSİZ',
                            'gtip_kodları': '8708' if '8708' in title.lower() else 'Yok',
                            'açıklama': title
                        })
                    except:
                        continue
            
            return results
            
        except Exception as e:
            print(f"❌ Google hatası: {e}")
            return []
    
    def display_results(self, results, company, country):
        """Sonuçları göster"""
        print(f"\n{'='*60}")
        print(f"📊 ANALİZ SONUÇLARI: {company} ↔ {country}")
        print(f"{'='*60}")
        
        if not results:
            print("✅ Hiçbir risk bulunamadı - Temiz")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n🔍 SONUÇ {i}:")
            print(f"   🌐 Site: {result.get('site', 'N/A')}")
            print(f"   📍 Ülke Bağlantısı: {result.get('ülke_bağlantısı', 'N/A')}")
            print(f"   🔢 GTIP Kodları: {result.get('gtip_kodları', 'N/A')}")
            print(f"   📝 Açıklama: {result.get('açıklama', 'N/A')}")
            print(f"   🔗 URL: {result.get('url', 'N/A')}")
            print(f"   {'─'*40}")

def main():
    print("🚀 BASİT TİCARET ANALİZ SİSTEMİ")
    print("💡 HEDEF: Hızlı ve etkili ticaret bağlantısı tespiti\n")
    
    analyzer = SimpleAnalyzer()
    
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 ANALİZ BAŞLATILIYOR...")
    start_time = time.time()
    
    results = analyzer.analyze(company, country)
    
    execution_time = time.time() - start_time
    
    analyzer.display_results(results, company, country)
    
    print(f"\n⏱️  Toplam süre: {execution_time:.2f} saniye")
    print(f"📊 Toplam sonuç: {len(results)}")

if __name__ == "__main__":
    main()
