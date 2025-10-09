import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from openpyxl import Workbook
from openpyxl.styles import Font
import matplotlib.pyplot as plt
import io
import json
import sys
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from functools import wraps
import os
from datetime import datetime
import xml.etree.ElementTree as ET

print("🚀 GELİŞMİŞ DUCKDUCKGO İLE GERÇEK ZAMANLI YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class Config:
    MAX_RESULTS: int = 3
    REQUEST_TIMEOUT: int = 10
    USER_AGENTS: List[str] = None
    
    def __post_init__(self):
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]

class AdvancedAIAnalyzer:
    def __init__(self, config: Config):
        self.config = config
    
    def extract_gtip_codes_from_text(self, text: str) -> List[str]:
        """Metinden GTIP/HS kodlarını çıkar"""
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
                    main_code = code[:4]
                    if main_code.isdigit():
                        all_codes.add(main_code)
        
        return list(all_codes)
    
    def smart_ai_analysis(self, text: str, company: str, country: str) -> Dict:
        """Yapay Zeka Analizi"""
        try:
            text_lower = text.lower()
            company_lower = company.lower()
            country_lower = country.lower()
            
            score = 0
            reasons = []
            
            # GTIP/HS kod çıkarımı
            gtip_codes = self.extract_gtip_codes_from_text(text)
            
            if gtip_codes:
                score += 40
                reasons.append(f"GTIP/HS kodları tespit edildi: {', '.join(gtip_codes)}")
            
            # Şirket ve ülke kontrolü
            company_found = any(word in text_lower for word in company_lower.split() if len(word) > 3)
            country_found = country_lower in text_lower
            
            if company_found:
                score += 30
                reasons.append("Şirket ismi bulundu")
            
            if country_found:
                score += 30
                reasons.append("Ülke ismi bulundu")
            
            # Ticaret terimleri
            trade_indicators = ['export', 'import', 'trade', 'business', 'partner', 'supplier']
            found_terms = [term for term in trade_indicators if term in text_lower]
            
            if found_terms:
                score += len(found_terms) * 5
                reasons.append(f"Ticaret terimleri: {', '.join(found_terms)}")
            
            # Risk seviyesi belirleme
            percentage = min(score, 100)
            
            if percentage >= 70:
                status = "YÜKSEK"
                explanation = f"✅ {company} şirketi {country} ile güçlü ticaret ilişkisi (%{percentage})"
            elif percentage >= 50:
                status = "ORTA"
                explanation = f"🟡 {company} şirketinin {country} ile ticaret olasılığı (%{percentage})"
            elif percentage >= 30:
                status = "DÜŞÜK"
                explanation = f"🟢 {company} şirketinin {country} ile sınırlı ticaret belirtileri (%{percentage})"
            else:
                status = "BELİRSİZ"
                explanation = f"⚪ {company} şirketinin {country} ile ticaret ilişkisi kanıtı yok (%{percentage})"
            
            return {
                'DURUM': status,
                'GÜVEN_YÜZDESİ': percentage,
                'AI_AÇIKLAMA': explanation,
                'AI_NEDENLER': ' | '.join(reasons),
                'TESPIT_EDILEN_GTIPLER': ', '.join(gtip_codes),
                'YAPTIRIM_RISKI': 'DÜŞÜK' if not gtip_codes else 'KONTROL_EDİLMELİ',
                'AI_TAVSIYE': 'Analiz tamamlandı. Sonuçları değerlendirin.'
            }
            
        except Exception as e:
            return {
                'DURUM': 'HATA',
                'GÜVEN_YÜZDESİ': 0,
                'AI_AÇIKLAMA': f'Analiz hatası: {str(e)}',
                'AI_NEDENLER': '',
                'TESPIT_EDILEN_GTIPLER': '',
                'YAPTIRIM_RISKI': 'BELİRSİZ',
                'AI_TAVSIYE': 'Tekrar deneyiniz.'
            }

class SearchEngineManager:
    def __init__(self, config: Config):
        self.config = config
    
    def duckduckgo_search(self, query: str) -> List[Dict]:
        """DuckDuckGo arama"""
        try:
            logging.info(f"DuckDuckGo'da aranıyor: {query}")
            
            # Basit mock veri - gerçek arama yapmıyoruz
            mock_results = [
                {
                    'title': f'{query} - Uluslararası Ticaret',
                    'snippet': f'{query} ile ilgili ticaret ve iş birliği fırsatları',
                    'url': 'https://example.com/1'
                },
                {
                    'title': f'{query} İhracat Bilgileri',
                    'snippet': f'{query} için ihracat ve ticaret rehberi',
                    'url': 'https://example.com/2'
                },
                {
                    'title': f'{query} Business Opportunities',
                    'snippet': f'{query} iş fırsatları ve ticaret ortaklıkları',
                    'url': 'https://example.com/3'
                }
            ]
            
            return mock_results
            
        except Exception as e:
            logging.error(f"Arama hatası: {e}")
            return []

def create_advanced_excel_report(results: List[Dict], company: str, country: str) -> str:
    """Gelişmiş Excel raporu oluştur ve dosya yolunu döndür"""
    try:
        # DataFrame oluştur
        df_data = []
        for result in results:
            row = {
                'ŞİRKET': result.get('ŞİRKET', ''),
                'ÜLKE': result.get('ÜLKE', ''),
                'DURUM': result.get('DURUM', ''),
                'GÜVEN_YÜZDESİ': result.get('GÜVEN_YÜZDESİ', 0),
                'YAPTIRIM_RISKI': result.get('YAPTIRIM_RISKI', ''),
                'TESPIT_EDILEN_GTIPLER': result.get('TESPIT_EDILEN_GTIPLER', ''),
                'AI_AÇIKLAMA': result.get('AI_AÇIKLAMA', ''),
                'AI_NEDENLER': result.get('AI_NEDENLER', ''),
                'AI_TAVSIYE': result.get('AI_TAVSIYE', ''),
                'ARAMA_SORGUSU': result.get('ARAMA_SORGUSU', ''),
                'BAŞLIK': result.get('BAŞLIK', ''),
                'URL': result.get('URL', ''),
                'ÖZET': result.get('ÖZET', '')
            }
            df_data.append(row)
        
        df_results = pd.DataFrame(df_data)
        
        # Excel dosyası oluştur
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "AI Analiz Sonuçları"
        
        # Başlıklar
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'GÜVEN_YÜZDESİ', 'YAPTIRIM_RISKI',
            'TESPIT_EDILEN_GTIPLER', 'AI_AÇIKLAMA', 'AI_NEDENLER', 
            'AI_TAVSIYE', 'ARAMA_SORGUSU', 'BAŞLIK', 'URL', 'ÖZET'
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header).font = Font(bold=True)
        
        # Veriler
        for row, result in enumerate(df_results.to_dict('records'), 2):
            for col, header in enumerate(headers, 1):
                ws.cell(row=row, column=col, value=str(result.get(header, '')))
        
        # Otomatik genişlik ayarı
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
        logging.info(f"Excel raporu oluşturuldu: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Excel rapor oluşturma hatası: {e}")
        return None

class AdvancedTradeAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self.search_engine = SearchEngineManager(config)
        self.ai_analyzer = AdvancedAIAnalyzer(config)
    
    def ai_enhanced_search(self, company: str, country: str) -> List[Dict]:
        """AI destekli gelişmiş ticaret analizi"""
        logging.info(f"🤖 AI DESTEKLİ ANALİZ: {company} ↔ {country}")
        
        search_queries = [
            f"{company} export {country}",
            f"{company} {country} business",
            f"{company} {country} trade",
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                logging.info(f"🔍 Arama: {query}")
                search_results = self.search_engine.duckduckgo_search(query)
                
                for result in search_results:
                    analysis_text = f"{result['title']} {result['snippet']}"
                    ai_analysis = self.ai_analyzer.smart_ai_analysis(analysis_text, company, country)
                    
                    combined_result = {
                        'ŞİRKET': company,
                        'ÜLKE': country,
                        'ARAMA_SORGUSU': query,
                        'BAŞLIK': result['title'],
                        'URL': result['url'],
                        'ÖZET': result['snippet'],
                        **ai_analysis
                    }
                    
                    all_results.append(combined_result)
                
                time.sleep(1)  # Kısa bekleme
                
            except Exception as e:
                logging.error(f"Search query error for '{query}': {e}")
                continue
        
        return all_results

def display_results(results: List[Dict], company: str, country: str):
    """Sonuçları ekranda göster"""
    print(f"\n{'='*80}")
    print(f"📊 ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Analiz sonucu bulunamadı!")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   📋 Özet: {result.get('ÖZET', 'N/A')[:100]}...")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   📈 Güven: %{result.get('GÜVEN_YÜZDESİ', 0)}")
        print(f"   ⚠️  Yaptırım Riski: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   📌 Nedenler: {result.get('AI_NEDENLER', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 GELİŞMİŞ DUCKDUCKGO İLE GERÇEK ZAMANLI YAPAY ZEKA YAPTIRIM ANALİZİ")
    print("🌐 ÖZELLİK: Mock Veri ile Hızlı Analiz")
    print("💡 NOT: Bu versiyon gerçek internet araması yapmaz, test verisi kullanır\n")
    
    # Yapılandırma
    config = Config()
    analyzer = AdvancedTradeAnalyzer(config)
    
    # Manuel giriş
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 AI ANALİZİ BAŞLATILIYOR: {company} ↔ {country}")
    print("⏳ Analiz yapılıyor, lütfen bekleyin...")
    
    results = analyzer.ai_enhanced_search(company, country)
    
    if results:
        # Sonuçları göster
        display_results(results, company, country)
        
        # Excel raporu oluştur
        filename = create_advanced_excel_report(results, company, country)
        
        if filename:
            print(f"\n✅ Excel raporu oluşturuldu: {filename}")
            
            # İstatistikler
            total_results = len(results)
            high_confidence = len([r for r in results if r.get('GÜVEN_YÜZDESİ', 0) >= 70])
            medium_confidence = len([r for r in results if 50 <= r.get('GÜVEN_YÜZDESİ', 0) < 70])
            low_confidence = len([r for r in results if r.get('GÜVEN_YÜZDESİ', 0) < 50])
            
            print(f"\n📈 İSTATİSTİKLER:")
            print(f"   • Toplam Sonuç: {total_results}")
            print(f"   • Yüksek Güven: {high_confidence}")
            print(f"   • Orta Güven: {medium_confidence}")
            print(f"   • Düşük Güven: {low_confidence}")
            
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
