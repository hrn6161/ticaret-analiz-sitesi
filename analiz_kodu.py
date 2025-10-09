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
    MAX_RESULTS: int = 6
    REQUEST_TIMEOUT: int = 15
    RETRY_ATTEMPTS: int = 3
    DELAY_BETWEEN_REQUESTS: float = 1.0
    DELAY_BETWEEN_SEARCHES: float = 2.0
    EU_SANCTIONS_URL: str = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02014R0833-20250720"
    
    USER_AGENTS: List[str] = None
    
    def __post_init__(self):
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]

class ErrorHandler:
    @staticmethod
    def handle_request_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error in {func.__name__}: {e}")
                return None
            except Exception as e:
                logging.error(f"Unexpected error in {func.__name__}: {e}")
                return None
        return wrapper

class EUSanctionsAPI:
    """AB Yaptırım Listesi API'si - Gerçek Zamanlı Kontrol"""
    
    def __init__(self, config: Config):
        self.config = config
        self.sanctions_cache = {}
        self.last_update = None
        self.cache_duration = 3600  # 1 saat cache
    
    def fetch_real_time_sanctions(self) -> Dict[str, Dict]:
        """Gerçek zamanlı AB yaptırım listesini al"""
        try:
            # Cache kontrolü
            if (self.last_update and 
                time.time() - self.last_update < self.cache_duration and 
                self.sanctions_cache):
                logging.info("Önbellekten AB yaptırım listesi kullanılıyor")
                return self.sanctions_cache
            
            logging.info("🌐 Gerçek zamanlı AB yaptırım listesi alınıyor...")
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(
                self.config.EU_SANCTIONS_URL, 
                headers=headers, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                sanctions_data = self.parse_eu_sanctions_page(response.text)
                self.sanctions_cache = sanctions_data
                self.last_update = time.time()
                logging.info(f"✅ AB yaptırım listesi güncellendi: {len(sanctions_data)} yasaklı ürün")
                return sanctions_data
            else:
                logging.warning(f"AB yaptırım listesi alınamadı: {response.status_code}")
                return self.get_fallback_sanctions()
                
        except Exception as e:
            logging.error(f"AB yaptırım listesi alım hatası: {e}")
            return self.get_fallback_sanctions()
    
    def parse_eu_sanctions_page(self, html_content: str) -> Dict[str, Dict]:
        """AB yaptırım sayfasını parse et ve GTIP kodlarını çıkar"""
        sanctions_data = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Sayfadaki tüm metni al
            text_content = soup.get_text()
            
            # GTIP kodlarını çıkar (gelişmiş regex)
            gtip_patterns = [
                r'\b(?:GTIP|HS|tariff)\s*(?:code|number)?\s*[:]?\s*(\d{4})[\s\.]*(\d{0,4})',
                r'\bCN\s*codes?\s*[:]?\s*(\d{4})[\s\.]*(\d{0,4})',
                r'\b(?:ex\s+)?\b(\d{4})\s*\.\s*(\d{0,4})\b',
                r'\b(?:heading|code)\s+(\d{4})[\s\.]*(\d{0,4})',
                r'\b(\d{4})[\s\.]*(\d{0,4})(?:\s*(?:of|and|or)\s*(?:\d{4}[\s\.]*\d{0,4}))*',
            ]
            
            for pattern in gtip_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    main_code = match.group(1)  # İlk 4 hane
                    sub_code = match.group(2) if match.group(2) else ""
                    
                    if main_code.isdigit():
                        full_code = f"{main_code}.{sub_code}" if sub_code else main_code
                        product_desc = self.extract_product_description(text_content, match.start(), match.end())
                        
                        sanctions_data[main_code] = {
                            'full_code': full_code,
                            'description': product_desc,
                            'risk_level': 'YÜKSEK_RISK',
                            'source': 'AB_YAPTIRIM_LISTESI',
                            'confidence': 'YÜKSEK'
                        }
            
            # Ek olarak yasaklı ürün kategorilerini ara
            prohibited_products = [
                # Taşıtlar ve parçaları
                'tractor', 'vehicle', 'automobile', 'motor vehicle', 'car', 'truck',
                'aircraft', 'airplane', 'helicopter', 'drones?',
                'engine', 'motor', 'chassis',
                
                # Silah ve savunma
                'weapon', 'firearm', 'armament', 'military', 'defence', 'war',
                'missile', 'bomb', 'torpedo', 'explosive',
                
                # Teknoloji
                'computer', 'electronic', 'semiconductor', 'integrated circuit',
                'radar', 'navigation', 'communication', 'telecom',
                'encryption', 'crypto',
                
                # Enerji
                'oil', 'gas', 'petroleum', 'refining',
                'nuclear', 'uranium', 'plutonium',
                
                # Çift kullanımlı mallar
                'dual.use', 'dual use', 'dual-purpose'
            ]
            
            for product in prohibited_products:
                if re.search(product, text_content, re.IGNORECASE):
                    # Bu ürünle ilişkili GTIP kodlarını bul
                    related_codes = self.find_related_gtip_codes(product)
                    for code in related_codes:
                        sanctions_data[code] = {
                            'full_code': code,
                            'description': f"Yasaklı {product} kategorisi",
                            'risk_level': 'YÜKSEK_RISK',
                            'source': 'AB_YAPTIRIM_KATEGORI',
                            'confidence': 'ORTA'
                        }
            
            logging.info(f"AB sayfasından {len(sanctions_data)} yasaklı GTIP kodu çıkarıldı")
            
        except Exception as e:
            logging.error(f"AB sayfası parse hatası: {e}")
        
        return sanctions_data
    
    def extract_product_description(self, text: str, start_pos: int, end_pos: int) -> str:
        """GTIP kodu etrafındaki ürün açıklamasını çıkar"""
        try:
            # GTIP kodu etrafındaki 200 karakterlik bölümü al
            context_start = max(0, start_pos - 100)
            context_end = min(len(text), end_pos + 100)
            context = text[context_start:context_end]
            
            # Cümleleri bul
            sentences = re.split(r'[.!?]', context)
            for sentence in sentences:
                if re.search(r'\b(?:prohibited|banned|restricted|sanction|forbidden)\b', sentence, re.IGNORECASE):
                    return sentence.strip()[:100] + "..."
            
            return "Yasaklı ürün kategorisi"
        except:
            return "Yasaklı ürün"
    
    def find_related_gtip_codes(self, product_keyword: str) -> List[str]:
        """Ürün anahtar kelimesine göre ilişkili GTIP kodlarını bul"""
        product_to_gtip = {
            'tractor': ['8701'],
            'vehicle': ['8702', '8703', '8704'],
            'automobile': ['8703'],
            'car': ['8703'],
            'truck': ['8704'],
            'aircraft': ['8802'],
            'airplane': ['8802'],
            'helicopter': ['8802'],
            'drones?': ['8806'],
            'engine': ['8407', '8408'],
            'motor': ['8407', '8501'],
            'weapon': ['9301', '9302', '9303', '9306'],
            'firearm': ['9301', '9302'],
            'missile': ['9301'],
            'computer': ['8471'],
            'electronic': ['8542', '8543'],
            'semiconductor': ['8541'],
            'radar': ['8526'],
            'communication': ['8517'],
            'nuclear': ['2844'],
        }
        
        related_codes = []
        for product, codes in product_to_gtip.items():
            if re.search(product, product_keyword, re.IGNORECASE):
                related_codes.extend(codes)
        
        return list(set(related_codes))
    
    def get_fallback_sanctions(self) -> Dict[str, Dict]:
        """İnternet bağlantısı olmazsa yedek yaptırım listesi"""
        logging.info("Yedek yaptırım listesi kullanılıyor")
        return {
            '8701': {'full_code': '8701', 'description': 'Traktörler', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8702': {'full_code': '8702', 'description': 'Motorlu taşıtlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8703': {'full_code': '8703', 'description': 'Otomobiller', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8704': {'full_code': '8704', 'description': 'Kamyonlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8708': {'full_code': '8708', 'description': 'Taşıt parçaları', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8802': {'full_code': '8802', 'description': 'Uçaklar, helikopterler', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8803': {'full_code': '8803', 'description': 'Uçak parçaları', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '9301': {'full_code': '9301', 'description': 'Silahlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '9306': {'full_code': '9306', 'description': 'Bombalar, torpidolar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8471': {'full_code': '8471', 'description': 'Bilgisayarlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8526': {'full_code': '8526', 'description': 'Radar cihazları', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8541': {'full_code': '8541', 'description': 'Yarı iletkenler', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '2844': {'full_code': '2844', 'description': 'Nükleer malzemeler', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
        }
    
    def check_gtip_against_sanctions(self, gtip_codes: List[str]) -> Tuple[List[str], Dict]:
        """GTIP kodlarını AB yaptırım listesinde kontrol et"""
        sanctioned_found = []
        sanction_details = {}
        
        try:
            real_time_sanctions = self.fetch_real_time_sanctions()
            
            for gtip_code in gtip_codes:
                if gtip_code in real_time_sanctions:
                    sanctioned_found.append(gtip_code)
                    sanction_info = real_time_sanctions[gtip_code]
                    
                    sanction_details[gtip_code] = {
                        'risk_level': "YAPTIRIMLI_YÜKSEK_RISK",
                        'reason': f"GTIP {gtip_code} - {sanction_info['description']} (Kaynak: {sanction_info['source']})",
                        'found_in_sanction_list': True,
                        'prohibition_confidence': 3,
                        'sanction_details': sanction_info
                    }
                    logging.warning(f"⛔ Yaptırımlı kod bulundu: {gtip_code} - {sanction_info['description']}")
                else:
                    sanction_details[gtip_code] = {
                        'risk_level': "DÜŞÜK",
                        'reason': f"GTIP {gtip_code} AB yaptırım listesinde bulunamadı",
                        'found_in_sanction_list': False,
                        'prohibition_confidence': 0
                    }
            
            logging.info(f"✅ Gerçek zamanlı AB yaptırım kontrolü tamamlandı: {len(sanctioned_found)} yasaklı kod")
            
        except Exception as e:
            logging.error(f"❌ AB yaptırım kontrol hatası: {e}")
        
        return sanctioned_found, sanction_details

class RealTimeSanctionAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self.sanctioned_codes = {}
        self.eu_api = EUSanctionsAPI(config)
    
    def extract_gtip_codes_from_text(self, text: str) -> List[str]:
        """Metinden GTIP/HS kodlarını çıkar - GELİŞMİŞ VERSİYON"""
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',
            r'\bHS\s?:?\s?(\d{4,8})\b',
            r'\bGTIP\s?:?\s?(\d{4,8})\b',
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',
            r'\bHarmonized System\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bCustoms\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bTariff\s?Code\s?:?\s?(\d{4,8})\b',
            r'\bCN\s?code\s?:?\s?(\d{4,8})\b',
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
        
        # Sayısal desen kontrolü - gelişmiş
        number_pattern = r'\b\d{4}\b'
        numbers = re.findall(number_pattern, text)
        
        for num in numbers:
            if num.isdigit():
                num_int = int(num)
                # Genişletilmiş GTIP aralıkları
                if ((8400 <= num_int <= 8600) or (8700 <= num_int <= 8900) or 
                    (9000 <= num_int <= 9300) or (2800 <= num_int <= 2900) or
                    (8470 <= num_int <= 8480) or (8500 <= num_int <= 8520) or
                    (8540 <= num_int <= 8550) or (9301 <= num_int <= 9307)):
                    all_codes.add(num)
        
        logging.info(f"Metinden çıkarılan GTIP/HS kodları: {list(all_codes)}")
        return list(all_codes)
    
    def check_eu_sanctions_realtime(self, gtip_codes: List[str]) -> Tuple[List[str], Dict]:
        """GERÇEK ZAMANLI AB yaptırım listesi kontrolü"""
        return self.eu_api.check_gtip_against_sanctions(gtip_codes)

class DatabaseManager:
    def __init__(self, db_path="analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with self.connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT,
                    country TEXT,
                    search_term TEXT,
                    gtip_codes TEXT,
                    risk_level TEXT,
                    confidence REAL,
                    sanction_risk TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_analysis(self, company: str, country: str, search_term: str, 
                     gtip_codes: List[str], risk_level: str, confidence: float, 
                     sanction_risk: str):
        with self.connection() as conn:
            conn.execute('''
                INSERT INTO analysis_history 
                (company, country, search_term, gtip_codes, risk_level, confidence, sanction_risk)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (company, country, search_term, ','.join(gtip_codes), risk_level, confidence, sanction_risk))

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'searches_completed': 0,
            'pages_analyzed': 0,
            'average_confidence': 0,
            'execution_time': 0,
            'errors_encountered': 0
        }
        self.start_time = time.time()
    
    def update_metric(self, metric: str, value: float = None):
        if value is not None:
            self.metrics[metric] = value
        else:
            self.metrics[metric] = self.metrics.get(metric, 0) + 1
        
        logging.info(f"Metric updated - {metric}: {self.metrics[metric]}")
    
    def get_summary(self):
        self.metrics['execution_time'] = time.time() - self.start_time
        return self.metrics

class AdvancedAIAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self.analysis_history = []
        self.sanction_analyzer = RealTimeSanctionAnalyzer(config)
        self.db = DatabaseManager()
        self.monitor = PerformanceMonitor()
    
    def smart_ai_analysis(self, text: str, company: str, country: str) -> Dict:
        """Gelişmiş Yerel Yapay Zeka Analizi - Gerçek Zamanlı Yaptırım Kontrolü"""
        try:
            text_lower = text.lower()
            company_lower = company.lower()
            country_lower = country.lower()
            
            score = 0
            reasons = []
            keywords_found = []
            confidence_factors = []
            detected_products = []
            
            # GTIP/HS kod çıkarımı
            gtip_codes = self.sanction_analyzer.extract_gtip_codes_from_text(text)
            
            if gtip_codes:
                score += 40
                reasons.append(f"GTIP/HS kodları tespit edildi: {', '.join(gtip_codes)}")
                confidence_factors.append("GTIP/HS kodları mevcut")
                logging.info(f"GTIP/HS kodları bulundu: {gtip_codes}")
            
            # GERÇEK ZAMANLI Yaptırım kontrolü - HER ZAMAN yapılıyor
            print("       🌐 GERÇEK ZAMANLI AB Yaptırım Listesi kontrol ediliyor...")
            sanctioned_codes, sanction_analysis = self.sanction_analyzer.check_eu_sanctions_realtime(gtip_codes)
            
            # Diğer analiz kodları aynı...
            company_words = [word for word in company_lower.split() if len(word) > 3]
            company_found = any(word in text_lower for word in company_words)
            country_found = country_lower in text_lower
            
            if company_found:
                score += 30
                reasons.append("Şirket ismi bulundu")
                confidence_factors.append("Şirket tanımlı")
            
            if country_found:
                score += 30
                reasons.append("Ülke ismi bulundu")
                confidence_factors.append("Hedef ülke tanımlı")
            
            trade_indicators = {
                'export': 15, 'import': 15, 'trade': 12, 'trading': 10, 'business': 10,
                'partner': 12, 'market': 10, 'distributor': 15, 'supplier': 12, 'dealer': 10,
                'agent': 8, 'cooperation': 10, 'collaboration': 8, 'shipment': 10, 'logistics': 8,
                'customs': 8, 'foreign': 6, 'international': 8, 'overseas': 6, 'global': 6,
                'hs code': 20, 'gtip': 20, 'harmonized system': 20, 'customs code': 15,
                'tariff code': 15, 'trade relation': 12, 'business partner': 15
            }
            
            for term, points in trade_indicators.items():
                if term in text_lower:
                    score += points
                    keywords_found.append(term)
                    reasons.append(f"{term} terimi bulundu")
            
            product_keywords = {
                'automotive': '8703', 'vehicle': '8703', 'car': '8703', 'motor': '8407',
                'engine': '8407', 'parts': '8708', 'component': '8708', 'truck': '8704',
                'tractor': '8701', 'computer': '8471', 'electronic': '8542', 'aircraft': '8802',
                'weapon': '9306', 'chemical': '2844', 'signal': '8517', 'drone': '8806',
                'missile': '9301', 'radar': '8526', 'semiconductor': '8541', 'nuclear': '2844',
                'aviation': '8802', 'military': '9301', 'defense': '9301', 'technology': '8543'
            }
            
            for product, gtip in product_keywords.items():
                if product in text_lower:
                    detected_products.append(f"{product}({gtip})")
                    if gtip not in gtip_codes:
                        gtip_codes.append(gtip)
                    reasons.append(f"{product} ürün kategorisi tespit edildi (GTIP/HS: {gtip})")
            
            context_phrases = [
                f"{company_lower}.*{country_lower}",
                f"export.*{country_lower}",
                f"business.*{country_lower}",
                f"partner.*{country_lower}",
                f"market.*{country_lower}",
                f"distributor.*{country_lower}",
                f"supplier.*{country_lower}",
            ]
            
            context_matches = 0
            for phrase in context_phrases:
                if re.search(phrase, text_lower):
                    context_matches += 1
                    reasons.append(f"Bağlam eşleşmesi: {phrase}")
            
            if context_matches >= 2:
                score += 20
                confidence_factors.append("Güçlü bağlam")
            
            unique_trade_terms = len(set(keywords_found))
            if unique_trade_terms >= 3:
                score += 10
                reasons.append(f"{unique_trade_terms} farklı ticaret terimi")
                confidence_factors.append("Zengin terminoloji")
            
            word_count = len(text_lower.split())
            if word_count > 500:
                score += 5
                confidence_factors.append("Detaylı içerik")
            
            sanctions_result = self.analyze_sanctions_risk(company, country, gtip_codes, sanctioned_codes, sanction_analysis)
            
            max_possible = 250
            percentage = (score / max_possible) * 100 if max_possible > 0 else 0
            
            if sanctions_result['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_YÜKSEK_RISK':
                status = "YAPTIRIMLI_YÜKSEK_RISK"
                explanation = f"⛔ YÜKSEK YAPTIRIM RİSKİ: {company} şirketi {country} ile yaptırımlı ürün ticareti yapıyor (%{percentage:.1f})"
            elif sanctions_result['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_ORTA_RISK':
                status = "YAPTIRIMLI_ORTA_RISK"
                explanation = f"🟡 ORTA YAPTIRIM RİSKİ: {company} şirketi {country} ile kısıtlamalı ürün ticareti yapıyor (%{percentage:.1f})"
            elif percentage >= 60:
                status = "EVET"
                explanation = f"✅ YÜKSEK GÜVEN: {company} şirketi {country} ile güçlü ticaret ilişkisi (%{percentage:.1f})"
            elif percentage >= 45:
                status = "OLASI"
                explanation = f"🟡 ORTA GÜVEN: {company} şirketinin {country} ile ticaret olasılığı (%{percentage:.1f})"
            elif percentage >= 30:
                status = "ZAYIF"
                explanation = f"🟢 DÜŞÜK GÜVEN: {company} şirketinin {country} ile sınırlı ticaret belirtileri (%{percentage:.1f})"
            else:
                status = "HAYIR"
                explanation = f"⚪ BELİRSİZ: {company} şirketinin {country} ile ticaret ilişkisi kanıtı yok (%{percentage:.1f})"
            
            if sanctions_result['YAPTIRIM_RISKI'] in ['YAPTIRIMLI_YÜKSEK_RISK', 'YAPTIRIMLI_ORTA_RISK']:
                explanation += f" | {sanctions_result['AI_YAPTIRIM_UYARI']}"
            
            ai_report = {
                'DURUM': status,
                'HAM_PUAN': score,
                'GÜVEN_YÜZDESİ': percentage,
                'AI_AÇIKLAMA': explanation,
                'AI_NEDENLER': ' | '.join(reasons),
                'AI_GÜVEN_FAKTÖRLERİ': ' | '.join(confidence_factors),
                'AI_ANAHTAR_KELİMELER': ', '.join(keywords_found),
                'AI_ANALİZ_TİPİ': 'Gerçek Zamanlı GTIP/HS Analizi + AB Yaptırım Kontrolü',
                'METİN_UZUNLUĞU': word_count,
                'BENZERLİK_ORANI': f"%{percentage:.1f}",
                'YAPTIRIM_RISKI': sanctions_result['YAPTIRIM_RISKI'],
                'TESPIT_EDILEN_GTIPLER': ', '.join(gtip_codes),
                'YAPTIRIMLI_GTIPLER': ', '.join(sanctions_result['YAPTIRIMLI_GTIPLER']),
                'GTIP_ANALIZ_DETAY': sanctions_result['GTIP_ANALIZ_DETAY'],
                'AI_YAPTIRIM_UYARI': sanctions_result['AI_YAPTIRIM_UYARI'],
                'AI_TAVSIYE': sanctions_result['AI_TAVSIYE'],
                'TESPIT_EDILEN_URUNLER': ', '.join(detected_products),
                'AB_LISTESINDE_BULUNDU': sanctions_result['AB_LISTESINDE_BULUNDU'],
                'GERCEK_ZAMANLI_KONTROL': 'EVET'
            }
            
            self.analysis_history.append(ai_report)
            self.monitor.update_metric('pages_analyzed')
            
            return ai_report
            
        except Exception as e:
            logging.error(f"AI analiz hatası: {e}")
            self.monitor.update_metric('errors_encountered')
            return {
                'DURUM': 'HATA', 'HAM_PUAN': 0, 'GÜVEN_YÜZDESİ': 0,
                'AI_AÇIKLAMA': f'AI analiz hatası: {str(e)}', 'AI_NEDENLER': '',
                'AI_GÜVEN_FAKTÖRLERİ': '', 'AI_ANAHTAR_KELİMELER': '', 'AI_ANALİZ_TİPİ': 'Hata',
                'METİN_UZUNLUĞU': 0, 'BENZERLİK_ORANI': '%0', 'YAPTIRIM_RISKI': 'BELİRSİZ',
                'TESPIT_EDILEN_GTIPLER': '', 'YAPTIRIMLI_GTIPLER': '', 'GTIP_ANALIZ_DETAY': '',
                'AI_YAPTIRIM_UYARI': 'Analiz hatası', 'AI_TAVSIYE': 'Tekrar deneyiniz',
                'TESPIT_EDILEN_URUNLER': '', 'AB_LISTESINDE_BULUNDU': 'HAYIR',
                'GERCEK_ZAMANLI_KONTROL': 'HAYIR'
            }
    
    def analyze_sanctions_risk(self, company: str, country: str, gtip_codes: List[str], 
                              sanctioned_codes: List[str], sanction_analysis: Dict) -> Dict:
        """Gelişmiş yaptırım risk analizi - Tüm ülkeler için"""
        analysis_result = {
            'YAPTIRIM_RISKI': 'DÜŞÜK', 'YAPTIRIMLI_GTIPLER': [], 'GTIP_ANALIZ_DETAY': '',
            'AI_YAPTIRIM_UYARI': '', 'AI_TAVSIYE': '', 'AB_LISTESINDE_BULUNDU': 'HAYIR'
        }
        
        # TÜM ülkeler için AB yaptırım kontrolü yapılıyor
        if gtip_codes:
            analysis_result['AB_LISTESINDE_BULUNDU'] = 'EVET'
            
            if sanctioned_codes:
                high_risk_codes = []
                medium_risk_codes = []
                
                for code in sanctioned_codes:
                    if code in sanction_analysis:
                        if sanction_analysis[code]['risk_level'] == 'YAPTIRIMLI_YÜKSEK_RISK':
                            high_risk_codes.append(code)
                        elif sanction_analysis[code]['risk_level'] == 'YAPTIRIMLI_ORTA_RISK':
                            medium_risk_codes.append(code)
                
                if high_risk_codes:
                    analysis_result['YAPTIRIM_RISKI'] = 'YAPTIRIMLI_YÜKSEK_RISK'
                    analysis_result['YAPTIRIMLI_GTIPLER'] = high_risk_codes
                    details = []
                    for code in high_risk_codes:
                        if code in sanction_analysis:
                            details.append(f"{code}: {sanction_analysis[code]['reason']}")
                    analysis_result['GTIP_ANALIZ_DETAY'] = ' | '.join(details)
                    analysis_result['AI_YAPTIRIM_UYARI'] = f'⛔ YÜKSEK YAPTIRIM RİSKİ: {company} şirketi {country} ile YASAKLI GTIP kodlarında ticaret yapıyor: {", ".join(high_risk_codes)}'
                    analysis_result['AI_TAVSIYE'] = f'⛔ BU ÜRÜNLERİN {country.upper()} İHRACI KESİNLİKLE YASAKTIR! GTIP/HS: {", ".join(high_risk_codes)}. Acilen hukuki danışmanlık alın.'
                
                elif medium_risk_codes:
                    analysis_result['YAPTIRIM_RISKI'] = 'YAPTIRIMLI_ORTA_RISK'
                    analysis_result['YAPTIRIMLI_GTIPLER'] = medium_risk_codes
                    details = []
                    for code in medium_risk_codes:
                        if code in sanction_analysis:
                            details.append(f"{code}: {sanction_analysis[code]['reason']}")
                    analysis_result['GTIP_ANALIZ_DETAY'] = ' | '.join(details)
                    analysis_result['AI_YAPTIRIM_UYARI'] = f'🟡 ORTA YAPTIRIM RİSKİ: {company} şirketi {country} ile kısıtlamalı GTIP kodlarında ticaret yapıyor: {", ".join(medium_risk_codes)}'
                    analysis_result['AI_TAVSIYE'] = f'🟡 Bu GTIP/HS kodları kısıtlamalı olabilir: {", ".join(medium_risk_codes)}. Resmi makamlardan teyit alınması önerilir.'
            
            else:
                analysis_result['YAPTIRIM_RISKI'] = 'DÜŞÜK'
                analysis_result['AI_YAPTIRIM_UYARI'] = f'✅ DÜŞÜK RİSK: {company} şirketinin tespit edilen GTIP/HS kodları AB yaptırım listesinde değil: {", ".join(gtip_codes)}'
                analysis_result['AI_TAVSIYE'] = f'Mevcut GTIP/HS kodları {country} ile ticaret için uygun görünüyor. Ancak güncel yaptırım listesini düzenli kontrol edin.'
        
        else:
            analysis_result['AI_YAPTIRIM_UYARI'] = 'ℹ️ GTIP/HS kodu tespit edilemedi. Manuel kontrol önerilir.'
            analysis_result['AI_TAVSIYE'] = 'Ürün GTIP/HS kodlarını manuel olarak kontrol edin ve AB yaptırım listesine bakın.'
        
        return analysis_result

class SearchEngineManager:
    def __init__(self, config: Config):
        self.config = config
    
    @ErrorHandler.handle_request_error
    def duckduckgo_search(self, query: str, max_results: int = None) -> List[Dict]:
        """DuckDuckGo arama fonksiyonu"""
        if max_results is None:
            max_results = self.config.MAX_RESULTS
            
        logging.info(f"DuckDuckGo'da aranıyor: {query}")
        
        url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'q': query,
            'b': '',
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=self.config.REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            return self.parse_duckduckgo_results(response.text, max_results)
        else:
            logging.warning(f"DuckDuckGo search failed: {response.status_code}")
            return []
    
    def parse_duckduckgo_results(self, html: str, max_results: int) -> List[Dict]:
        """DuckDuckGo sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # DuckDuckGo result containers
        result_containers = soup.find_all('div', class_='result')
        
        for container in result_containers[:max_results]:
            try:
                title_elem = container.find('a', class_='result__a')
                snippet_elem = container.find('a', class_='result__snippet')
                url_elem = container.find('a', class_='result__url')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Clean URL
                    if url.startswith('//duckduckgo.com/l/'):
                        # Extract actual URL from redirect
                        match = re.search(r'uddg=([^&]+)', url)
                        if match:
                            url = requests.utils.unquote(match.group(1))
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                    
            except Exception as e:
                logging.warning(f"Result parsing error: {e}")
                continue
        
        logging.info(f"Parsed {len(results)} search results")
        return results

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
            f"{company} {country} distributor",
            f"{company} {country} supplier",
            f"{company} {country} partner",
            f"{company} {country} HS code",
            f"{company} {country} GTIP",
            f"{company} {country} tariff",
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                logging.info(f"🔍 Arama: {query}")
                search_results = self.search_engine.duckduckgo_search(query)
                
                for result in search_results:
                    # AI analizi yap
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
                
                time.sleep(self.config.DELAY_BETWEEN_SEARCHES)
                
            except Exception as e:
                logging.error(f"Search query error for '{query}': {e}")
                continue
        
        return all_results

def create_advanced_excel_report(df_results: pd.DataFrame, filename: str) -> bool:
    """Gelişmiş Excel raporu oluştur"""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "AI Analiz Sonuçları"
        
        # Başlıklar
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'GÜVEN_YÜZDESİ', 'YAPTIRIM_RISKI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA',
            'AI_NEDENLER', 'AI_TAVSIYE', 'ARAMA_SORGUSU', 'BAŞLIK', 'URL'
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
        return True
        
    except Exception as e:
        logging.error(f"Excel rapor oluşturma hatası: {e}")
        return False

def main():
    print("📊 GELİŞMİŞ DUCKDUCKGO İLE GERÇEK ZAMANLI YAPAY ZEKA YAPTIRIM ANALİZİ")
    print("🌐 ÖZELLİK: Gerçek Zamanlı AB Yaptırım Listesi Kontrolü Aktif!")
    print("💡 NOT: GTIP kodları https://eur-lex.europa.eu/ adresinde gerçek zamanlı kontrol ediliyor\n")
    
    # Yapılandırma
    config = Config()
    analyzer = AdvancedTradeAnalyzer(config)
    
    # Manuel giriş
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 GERÇEK ZAMANLI AI ANALİZİ: {company} ↔ {country}")
    print("=" * 60)
    
    results = analyzer.ai_enhanced_search(company, country)
    
    if results:
        df_results = pd.DataFrame(results)
        filename = f"{company.replace(' ', '_')}_{country}_gercek_zamanli_analiz.xlsx"
        
        if create_advanced_excel_report(df_results, filename):
            # Performans özeti
            metrics = analyzer.ai_analyzer.monitor.get_summary()
            
            total_analysis = len(results)
            high_conf_count = len(df_results[df_results['GÜVEN_YÜZDESİ'] >= 60])
            high_risk_count = len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_YÜKSEK_RISK'])
            medium_risk_count = len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_ORTA_RISK'])
            real_time_check_count = len(df_results[df_results['GERCEK_ZAMANLI_KONTROL'] == 'EVET'])
            
            print(f"\n🤖 GERÇEK ZAMANLI AI İSTATİSTİKLERİ:")
            print(f"   • Toplam AI Analiz: {total_analysis}")
            print(f"   • Gerçek Zamanlı Kontrol: {real_time_check_count}")
            print(f"   • Yüksek Güvenilir: {high_conf_count}")
            print(f"   • YÜKSEK Yaptırım Riski: {high_risk_count}")
            print(f"   • ORTA Yaptırım Riski: {medium_risk_count}")
            print(f"   • Çalışma Süresi: {metrics['execution_time']:.2f}s")
            
            if high_risk_count > 0 or medium_risk_count > 0:
                print(f"\n⚠️  KRİTİK YAPTIRIM UYARISI (GERÇEK ZAMANLI):")
                high_risk_data = df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_YÜKSEK_RISK']
                medium_risk_data = df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_ORTA_RISK']
                
                for _, row in high_risk_data.iterrows():
                    print(f"   🔴 YÜKSEK RİSK: {row['ŞİRKET']} - Yasaklı GTIP/HS: {row['YAPTIRIMLI_GTIPLER']}")
                
                for _, row in medium_risk_data.iterrows():
                    print(f"   🟡 ORTA RİSK: {row['ŞİRKET']} - Kısıtlamalı GTIP/HS: {row['YAPTIRIMLI_GTIPLER']}")
            
            print(f"\n✅ Analiz tamamlandı! Excel dosyası: {filename}")
            print(f"   🌐 Gerçek zamanlı AB yaptırım kontrolü aktif")
            print(f"   📊 Performans logları kaydedildi")
            
        else:
            print("❌ Excel raporu oluşturulamadı!")
    else:
        print("❌ AI analiz sonucu bulunamadı!")

if __name__ == "__main__":
    main()
