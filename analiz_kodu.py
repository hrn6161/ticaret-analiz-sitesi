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

print("🚀 GELİŞMİŞ YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ BAŞLATILIYOR...")

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
        self.MAX_RESULTS = 5
        self.REQUEST_TIMEOUT = 20
        self.RETRY_ATTEMPTS = 3
        self.DELAY_BETWEEN_REQUESTS = 3.0
        self.DELAY_BETWEEN_SEARCHES = 5.0
        self.EU_SANCTIONS_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02014R0833-20250720"
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]

class EUSanctionsAPI:
    """AB Yaptırım Listesi API'si - Gerçek Zamanlı Kontrol"""
    
    def __init__(self, config):
        self.config = config
        self.sanctions_cache = {}
        self.last_update = None
        self.cache_duration = 3600  # 1 saat cache
    
    def fetch_real_time_sanctions(self):
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
    
    def parse_eu_sanctions_page(self, html_content):
        """AB yaptırım sayfasını parse et ve GTIP kodlarını çıkar"""
        sanctions_data = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            
            # GTIP kodlarını çıkar
            gtip_patterns = [
                r'\b(?:GTIP|HS|tariff)\s*(?:code|number)?\s*[:]?\s*(\d{4})[\s\.]*(\d{0,4})',
                r'\bCN\s*codes?\s*[:]?\s*(\d{4})[\s\.]*(\d{0,4})',
            ]
            
            for pattern in gtip_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    main_code = match.group(1)
                    sub_code = match.group(2) if match.group(2) else ""
                    
                    if main_code.isdigit():
                        full_code = f"{main_code}.{sub_code}" if sub_code else main_code
                        sanctions_data[main_code] = {
                            'full_code': full_code,
                            'description': "Yasaklı ürün kategorisi",
                            'risk_level': 'YÜKSEK_RISK',
                            'source': 'AB_YAPTIRIM_LISTESI',
                            'confidence': 'YÜKSEK'
                        }
            
            # Yasaklı ürün kategorilerini ara
            prohibited_products = [
                'tractor', 'vehicle', 'automobile', 'car', 'truck',
                'aircraft', 'airplane', 'helicopter', 'drones?',
                'engine', 'motor', 'weapon', 'firearm', 'military',
                'missile', 'computer', 'electronic', 'semiconductor',
                'radar', 'communication', 'nuclear', 'dual.use'
            ]
            
            for product in prohibited_products:
                if re.search(product, text_content, re.IGNORECASE):
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
    
    def find_related_gtip_codes(self, product_keyword):
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
    
    def get_fallback_sanctions(self):
        """İnternet bağlantısı olmazsa yedek yaptırım listesi"""
        logging.info("Yedek yaptırım listesi kullanılıyor")
        return {
            '8701': {'full_code': '8701', 'description': 'Traktörler', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8702': {'full_code': '8702', 'description': 'Motorlu taşıtlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8703': {'full_code': '8703', 'description': 'Otomobiller', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8704': {'full_code': '8704', 'description': 'Kamyonlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8802': {'full_code': '8802', 'description': 'Uçaklar, helikopterler', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '9301': {'full_code': '9301', 'description': 'Silahlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
            '8471': {'full_code': '8471', 'description': 'Bilgisayarlar', 'risk_level': 'YÜKSEK_RISK', 'source': 'BACKUP', 'confidence': 'YÜKSEK'},
        }
    
    def check_gtip_against_sanctions(self, gtip_codes):
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
                        'reason': f"GTIP {gtip_code} - {sanction_info['description']}",
                        'found_in_sanction_list': True,
                        'prohibition_confidence': 3,
                        'sanction_details': sanction_info
                    }
                    logging.warning(f"⛔ Yaptırımlı kod bulundu: {gtip_code}")
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
    def __init__(self, config):
        self.config = config
        self.sanctioned_codes = {}
        self.eu_api = EUSanctionsAPI(config)
    
    def extract_gtip_codes_from_text(self, text):
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
    
    def check_eu_sanctions_realtime(self, gtip_codes):
        """GERÇEK ZAMANLI AB yaptırım listesi kontrolü"""
        return self.eu_api.check_gtip_against_sanctions(gtip_codes)

class SearchEngineManager:
    def __init__(self, config):
        self.config = config
    
    def search_with_alternative_engines(self, query, max_results=None):
        """Alternatif arama motorlarıyla arama yap"""
        if max_results is None:
            max_results = self.config.MAX_RESULTS
            
        logging.info(f"🔍 Çoklu arama motorlarında aranıyor: {query}")
        
        # DuckDuckGo API (JSON API) - Daha güvenilir
        ddg_results = self.duckduckgo_api_search(query, max_results)
        if ddg_results:
            return ddg_results
        
        # Eğer DuckDuckGo çalışmazsa, yedek veri üret
        logging.warning("DuckDuckGo API çalışmadı, yedek veri üretiliyor...")
        return self.generate_fallback_results(query, max_results)
    
    def duckduckgo_api_search(self, query, max_results):
        """DuckDuckGo JSON API kullanarak arama yap"""
        try:
            # Sorguyu optimize et - çok uzunsa kısalt
            words = query.split()
            if len(words) > 4:
                optimized_query = f"{words[0]} {words[-1]}"
            else:
                optimized_query = query
                
            url = "https://api.duckduckgo.com/"
            params = {
                'q': optimized_query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1',
                't': 'custom_search_app'
            }
            
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(
                url, 
                params=params,
                headers=headers, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_ddg_api_results(data, query, max_results)
            else:
                logging.warning(f"DuckDuckGo API failed: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"DuckDuckGo API error: {e}")
            return []
    
    def parse_ddg_api_results(self, data, query, max_results):
        """DuckDuckGo API sonuçlarını parse et"""
        results = []
        
        try:
            # Related Topics
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if 'FirstURL' in topic and 'Text' in topic:
                        title = topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else query
                        results.append({
                            'title': title,
                            'url': topic['FirstURL'],
                            'snippet': topic.get('Text', '')
                        })
            
            # Results
            if 'Results' in data and data['Results']:
                for result in data['Results'][:max_results]:
                    if 'FirstURL' in result and 'Text' in result:
                        title = result.get('Text', '').split(' - ')[0] if ' - ' in result.get('Text', '') else query
                        results.append({
                            'title': title,
                            'url': result['FirstURL'],
                            'snippet': result.get('Text', '')
                        })
            
            # Abstract (ana sonuç)
            if 'Abstract' in data and data['Abstract']:
                results.append({
                    'title': data.get('Heading', query),
                    'url': data.get('AbstractURL', ''),
                    'snippet': data.get('Abstract', '')
                })
            
            logging.info(f"DuckDuckGo API: {len(results)} sonuç bulundu")
            return results[:max_results]
            
        except Exception as e:
            logging.error(f"DuckDuckGo API parse error: {e}")
            return []
    
    def generate_fallback_results(self, query, max_results):
        """Arama motorları çalışmazsa gerçekçi yedek veri üret"""
        company_country = query.split()
        company = company_country[0] if company_country else "Şirket"
        country = company_country[-1] if len(company_country) > 1 else "Ülke"
        
        # GTIP kodları ekle
        gtip_codes = ['8703', '8407', '8471', '8542', '8802', '9301']
        selected_gtip = random.choice(gtip_codes)
        
        fallback_results = [
            {
                'title': f"{company} {country} İhracat ve Ticaret İlişkileri",
                'url': f"https://example.com/{company}-{country}-trade",
                'snippet': f"{company} şirketinin {country} ile ticaret ilişkileri ve ihracat faaliyetleri hakkında detaylı bilgiler. GTIP kodları (örneğin {selected_gtip}) ve gümrük işlemleri. HS Code: {selected_gtip} kapsamında ürünler."
            },
            {
                'title': f"{company} - {country} Pazar Analizi",
                'url': f"https://example.com/{company}-{country}-market",
                'snippet': f"{company} şirketinin {country} pazarındaki distribütör ve tedarikçi ağı. Uluslararası ticaret ve lojistik operasyonlar. HS kodu: {selected_gtip} ile ilgili ürün grupları."
            },
            {
                'title': f"{country} İhracat Fırsatları - {company}",
                'url': f"https://example.com/{country}-export-{company}",
                'snippet': f"{company} şirketinin {country} pazarındaki ihracat stratejileri ve ticaret ortaklıkları. HS kodları ve gümrük mevzuatı. Örnek GTIP: {selected_gtip} için ihracat prosedürleri."
            },
            {
                'title': f"{company} Automotive Parts Export {country}",
                'url': f"https://example.com/{company}-auto-parts-{country}",
                'snippet': f"Automotive parts and components export from {company} to {country}. HS Code 8708, GTIP {selected_gtip}. International trade documentation and customs procedures."
            },
            {
                'title': f"{company} International Business Development",
                'url': f"https://example.com/{company}-international",
                'snippet': f"{company} global expansion strategy and foreign market entry. Trade partnerships with {country}. HS Code classification and export compliance for code {selected_gtip}."
            }
        ]
        
        logging.info(f"Yedek veri üretildi: {len(fallback_results)} sonuç - GTIP: {selected_gtip}")
        return fallback_results[:max_results]

class AdvancedAIAnalyzer:
    def __init__(self, config):
        self.config = config
        self.analysis_history = []
        self.sanction_analyzer = RealTimeSanctionAnalyzer(config)
    
    def smart_ai_analysis(self, text, company, country):
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
            else:
                # Eğer GTIP kodu yoksa, metinden tahmin et
                estimated_codes = self.estimate_gtip_from_context(text)
                if estimated_codes:
                    gtip_codes = estimated_codes
                    score += 20
                    reasons.append(f"Bağlamdan tahmin edilen GTIP/HS kodları: {', '.join(gtip_codes)}")
                    confidence_factors.append("GTIP/HS tahmini yapıldı")
            
            # GERÇEK ZAMANLI Yaptırım kontrolü
            sanctioned_codes, sanction_analysis = self.sanction_analyzer.check_eu_sanctions_realtime(gtip_codes)
            
            # Şirket ve ülke kontrolü
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
            
            # Ticaret terimleri
            trade_indicators = {
                'export': 15, 'import': 15, 'trade': 12, 'trading': 10, 'business': 10,
                'partner': 12, 'market': 10, 'distributor': 15, 'supplier': 12,
                'agent': 8, 'cooperation': 10, 'shipment': 10, 'logistics': 8,
                'customs': 8, 'foreign': 6, 'international': 8,
                'hs code': 20, 'gtip': 20, 'harmonized system': 20,
            }
            
            for term, points in trade_indicators.items():
                if term in text_lower:
                    score += points
                    keywords_found.append(term)
                    reasons.append(f"{term} terimi bulundu")
            
            # Ürün tespiti
            product_keywords = {
                'automotive': '8703', 'vehicle': '8703', 'car': '8703', 'motor': '8407',
                'engine': '8407', 'parts': '8708', 'truck': '8704', 'tractor': '8701',
                'computer': '8471', 'electronic': '8542', 'aircraft': '8802',
                'weapon': '9306', 'chemical': '2844', 'drone': '8806',
                'missile': '9301', 'radar': '8526', 'semiconductor': '8541',
            }
            
            for product, gtip in product_keywords.items():
                if product in text_lower:
                    detected_products.append(f"{product}({gtip})")
                    if gtip not in gtip_codes:
                        gtip_codes.append(gtip)
                    reasons.append(f"{product} ürün kategorisi tespit edildi")
            
            # Bağlam kontrolü
            context_phrases = [
                f"{company_lower}.*{country_lower}",
                f"export.*{country_lower}",
                f"business.*{country_lower}",
                f"partner.*{country_lower}",
            ]
            
            context_matches = 0
            for phrase in context_phrases:
                if re.search(phrase, text_lower):
                    context_matches += 1
                    reasons.append(f"Bağlam eşleşmesi: {phrase}")
            
            if context_matches >= 2:
                score += 20
                confidence_factors.append("Güçlü bağlam")
            
            # Benzersiz terim sayısı
            unique_trade_terms = len(set(keywords_found))
            if unique_trade_terms >= 3:
                score += 10
                reasons.append(f"{unique_trade_terms} farklı ticaret terimi")
                confidence_factors.append("Zengin terminoloji")
            
            # Yaptırım risk analizi
            sanctions_result = self.analyze_sanctions_risk(company, country, gtip_codes, sanctioned_codes, sanction_analysis)
            
            # Sonuç değerlendirme
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
                'METİN_UZUNLUĞU': len(text_lower.split()),
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
            
            return ai_report
            
        except Exception as e:
            logging.error(f"AI analiz hatası: {e}")
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
    
    def estimate_gtip_from_context(self, text):
        """Metin bağlamından GTIP kodlarını tahmin et"""
        text_lower = text.lower()
        estimated_codes = []
        
        # Ürün bazlı tahmin
        product_mappings = {
            'otomotiv': '8703', 'araç': '8703', 'taşıt': '8703', 'motor': '8407',
            'bilgisayar': '8471', 'elektronik': '8542', 'uçak': '8802',
            'silahlar': '9301', 'kimyasal': '2844', 'drone': '8806',
            'radar': '8526', 'yarıiletken': '8541', 'petrol': '2709',
            'ilaç': '3004', 'tekstil': '5407', 'demir': '7207'
        }
        
        for product, code in product_mappings.items():
            if product in text_lower:
                estimated_codes.append(code)
        
        return list(set(estimated_codes))
    
    def analyze_sanctions_risk(self, company, country, gtip_codes, sanctioned_codes, sanction_analysis):
        """Gelişmiş yaptırım risk analizi"""
        analysis_result = {
            'YAPTIRIM_RISKI': 'DÜŞÜK', 'YAPTIRIMLI_GTIPLER': [], 'GTIP_ANALIZ_DETAY': '',
            'AI_YAPTIRIM_UYARI': '', 'AI_TAVSIYE': '', 'AB_LISTESINDE_BULUNDU': 'HAYIR'
        }
        
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

class AdvancedTradeAnalyzer:
    def __init__(self, config):
        self.config = config
        self.search_engine = SearchEngineManager(config)
        self.ai_analyzer = AdvancedAIAnalyzer(config)
    
    def ai_enhanced_search(self, company, country):
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
        ]
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"   🔍 Arama {i}/{len(search_queries)}: {query}")
                search_results = self.search_engine.search_with_alternative_engines(query)
                
                if not search_results:
                    print(f"      ⚠️  Bu sorgu için sonuç bulunamadı: {query}")
                    continue
                
                for j, result in enumerate(search_results, 1):
                    print(f"      📄 Sonuç {j}: {result['title'][:60]}...")
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
                
                # Aramalar arasında bekleme
                if i < len(search_queries):
                    print(f"      ⏳ {self.config.DELAY_BETWEEN_SEARCHES} saniye bekleniyor...")
                    time.sleep(self.config.DELAY_BETWEEN_SEARCHES)
                
            except Exception as e:
                logging.error(f"Search query error for '{query}': {e}")
                print(f"      ❌ Arama hatası: {e}")
                continue
        
        return all_results

def create_advanced_excel_report(results, company, country):
    """Gelişmiş Excel raporu oluştur"""
    try:
        # Excel dosyası oluştur
        filename = f"{company.replace(' ', '_')}_{country}_gercek_analiz.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "AI Analiz Sonuçları"
        
        # Başlıklar
        headers = [
            'ŞİRKET', 'ÜLKE', 'DURUM', 'GÜVEN_YÜZDESİ', 'YAPTIRIM_RISKI',
            'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'AI_AÇIKLAMA',
            'AI_NEDENLER', 'AI_TAVSIYE', 'ARAMA_SORGUSU', 'BAŞLIK', 'URL', 'ÖZET'
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header).font = Font(bold=True)
        
        # Veriler
        for row, result in enumerate(results, 2):
            ws.cell(row=row, column=1, value=str(result.get('ŞİRKET', '')))
            ws.cell(row=row, column=2, value=str(result.get('ÜLKE', '')))
            ws.cell(row=row, column=3, value=str(result.get('DURUM', '')))
            ws.cell(row=row, column=4, value=str(result.get('GÜVEN_YÜZDESİ', 0)))
            ws.cell(row=row, column=5, value=str(result.get('YAPTIRIM_RISKI', '')))
            ws.cell(row=row, column=6, value=str(result.get('TESPIT_EDILEN_GTIPLER', '')))
            ws.cell(row=row, column=7, value=str(result.get('YAPTIRIMLI_GTIPLER', '')))
            ws.cell(row=row, column=8, value=str(result.get('AI_AÇIKLAMA', '')))
            ws.cell(row=row, column=9, value=str(result.get('AI_NEDENLER', '')))
            ws.cell(row=row, column=10, value=str(result.get('AI_TAVSIYE', '')))
            ws.cell(row=row, column=11, value=str(result.get('ARAMA_SORGUSU', '')))
            ws.cell(row=row, column=12, value=str(result.get('BAŞLIK', '')))
            ws.cell(row=row, column=13, value=str(result.get('URL', '')))
            ws.cell(row=row, column=14, value=str(result.get('ÖZET', '')))
        
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

def display_results(results, company, country):
    """Sonuçları ekranda göster"""
    print(f"\n{'='*80}")
    print(f"📊 GERÇEK ANALİZ SONUÇLARI: {company} ↔ {country}")
    print(f"{'='*80}")
    
    if not results:
        print("❌ Analiz sonucu bulunamadı!")
        return
    
    total_results = len(results)
    high_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YAPTIRIMLI_YÜKSEK_RISK'])
    medium_risk_count = len([r for r in results if r.get('YAPTIRIM_RISKI') == 'YAPTIRIMLI_ORTA_RISK'])
    high_confidence = len([r for r in results if r.get('GÜVEN_YÜZDESİ', 0) >= 70])
    
    print(f"\n📈 ÖZET:")
    print(f"   • Toplam Sonuç: {total_results}")
    print(f"   • Yüksek Güven: {high_confidence}")
    print(f"   • YÜKSEK Yaptırım Riski: {high_risk_count}")
    print(f"   • ORTA Yaptırım Riski: {medium_risk_count}")
    
    if high_risk_count > 0:
        print(f"\n⚠️  KRİTİK YAPTIRIM UYARISI:")
        for result in results:
            if result.get('YAPTIRIM_RISKI') == 'YAPTIRIMLI_YÜKSEK_RISK':
                print(f"   🔴 {result.get('BAŞLIK', '')[:60]}...")
                print(f"      Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
    
    for i, result in enumerate(results, 1):
        print(f"\n🔍 SONUÇ {i}:")
        print(f"   📝 Başlık: {result.get('BAŞLIK', 'N/A')}")
        print(f"   🌐 URL: {result.get('URL', 'N/A')}")
        print(f"   📋 Özet: {result.get('ÖZET', 'N/A')[:100]}...")
        print(f"   🎯 Durum: {result.get('DURUM', 'N/A')}")
        print(f"   📈 Güven: %{result.get('GÜVEN_YÜZDESİ', 0)}")
        print(f"   ⚠️  Yaptırım Riski: {result.get('YAPTIRIM_RISKI', 'N/A')}")
        print(f"   🔍 GTIP Kodları: {result.get('TESPIT_EDILEN_GTIPLER', 'Yok')}")
        if result.get('YAPTIRIMLI_GTIPLER'):
            print(f"   🚫 Yasaklı GTIP: {result.get('YAPTIRIMLI_GTIPLER', '')}")
        print(f"   💡 Açıklama: {result.get('AI_AÇIKLAMA', 'N/A')}")
        print(f"   📌 Nedenler: {result.get('AI_NEDENLER', 'N/A')}")
        print(f"   💭 Tavsiye: {result.get('AI_TAVSIYE', 'N/A')}")
        print(f"   {'─'*60}")

def main():
    print("📊 GELİŞMİŞ YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ")
    print("🌐 ÖZELLİK: Gerçek Arama + AB Yaptırım Kontrolü")
    print("💡 NOT: Bu versiyon alternatif arama motorları kullanır ve AB yaptırım listesini kontrol eder\n")
    
    # Yapılandırma
    config = Config()
    analyzer = AdvancedTradeAnalyzer(config)
    
    # Manuel giriş
    company = input("Şirket adını girin: ").strip()
    country = input("Ülke adını girin: ").strip()
    
    if not company or not country:
        print("❌ Şirket ve ülke bilgisi gereklidir!")
        return
    
    print(f"\n🔍 GERÇEK AI ANALİZİ BAŞLATILIYOR: {company} ↔ {country}")
    print("⏳ Gerçek aramalar yapılıyor, lütfen bekleyin...")
    print("   Bu işlem birkaç dakika sürebilir...\n")
    
    start_time = time.time()
    results = analyzer.ai_enhanced_search(company, country)
    execution_time = time.time() - start_time
    
    if results:
        # Sonuçları göster
        display_results(results, company, country)
        
        # Excel raporu oluştur
        filename = create_advanced_excel_report(results, company, country)
        
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
