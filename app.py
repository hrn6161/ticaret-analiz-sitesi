import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from openpyxl import Workbook
from openpyxl.styles import Font
import os
from datetime import datetime

print("🚀 DUCKDUCKGO İLE GERÇEK ZAMANLI YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ BAŞLATILIYOR...")

class RealTimeSanctionAnalyzer:
    def __init__(self):
        self.sanctioned_codes = {}
        
    def extract_gtip_codes_from_text(self, text):
        """Metinden GTIP/HS kodlarını çıkar - GELİŞMİŞ VERSİYON"""
        # Geliştirilmiş pattern: 4, 6, 8 haneli kodlar ve HS code formatları
        patterns = [
            r'\b\d{4}\.?\d{0,4}\b',  # 8703.21.00 gibi
            r'\bHS\s?CODE\s?:?\s?(\d{4,8})\b',  # HS CODE: 8703
            r'\bHS\s?:?\s?(\d{4,8})\b',  # HS: 8703
            r'\bGTIP\s?:?\s?(\d{4,8})\b',  # GTIP: 8703
            r'\bH\.S\.\s?CODE?\s?:?\s?(\d{4,8})\b',  # H.S. CODE: 8703
            r'\bHarmonized System\s?Code\s?:?\s?(\d{4,8})\b',  # Harmonized System Code: 8703
        ]
        
        all_codes = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Grup yakalama durumu
                
                # Sadece sayısal kısmı al
                code = re.sub(r'[^\d]', '', match)
                if len(code) >= 4:
                    main_code = code[:4]  # İlk 4 hane ana kod
                    if main_code.isdigit():
                        all_codes.add(main_code)
        
        # Ek olarak metinde geçen 4 haneli sayıları da kontrol et (yanlış pozitifleri azaltmak için)
        number_pattern = r'\b\d{4}\b'
        numbers = re.findall(number_pattern, text)
        
        # Yüksek olasılıklı GTIP kodları (8700-8900 arası genellikle makina/taşıt)
        for num in numbers:
            if num.isdigit():
                num_int = int(num)
                # Makina, taşıt, elektronik gibi kategori aralıkları
                if (8400 <= num_int <= 8600) or (8700 <= num_int <= 8900) or (9000 <= num_int <= 9300):
                    all_codes.add(num)
        
        return list(all_codes)
    
    def check_eu_sanctions_realtime(self, gtip_codes):
        """AB yaptırım listesini kontrol et - GENİŞLETİLMİŞ"""
        sanctioned_found = []
        sanction_details = {}
        
        try:
            print("       🌐 AB Yaptırım Listesi kontrol ediliyor...")
            
            # GENİŞLETİLMİŞ yaptırımlı kod listesi
            predefined_sanctions = {
                # Taşıtlar ve parçaları
                '8701': "Traktörler",
                '8702': "Motorlu taşıtlar",
                '8703': "Otomobiller, yük taşıtları",
                '8704': "Kamyonlar",
                '8705': "Özel amaçlı taşıtlar",
                '8706': "Şasiler",
                '8707': "Motorlar",
                '8708': "Taşıt parçaları",
                
                # Havacılık
                '8802': "Uçaklar, helikopterler",
                '8803': "Uçak parçaları",
                
                # Silahlar
                '9301': "Silahlar",
                '9302': "Tabancalar",
                '9303': "Tüfekler",
                '9306': "Bombalar, torpidolar",
                
                # Elektronik ve haberleşme
                '8471': "Bilgisayarlar",
                '8526': "Radar cihazları",
                '8542': "Entegre devreler",
                '8543': "Elektronik cihazlar",
                
                # Makinalar
                '8407': "İçten yanmalı motorlar",
                '8408': "Dizel motorlar",
                '8409': "Motor parçaları",
                
                # Diğer stratejik ürünler
                '8479': "Makinalar",
                '8501': "Elektrik motorları",
                '8517': "Telekom cihazları",
                '8525': "Kamera sistemleri",
                '8529': "Radyo cihazları",
                '8531': "Elektrik cihazları",
                '8541': "Yarı iletkenler"
            }
            
            for gtip_code in gtip_codes:
                if gtip_code in predefined_sanctions:
                    sanctioned_found.append(gtip_code)
                    product_name = predefined_sanctions[gtip_code]
                    sanction_details[gtip_code] = {
                        'risk_level': "YAPTIRIMLI_YÜKSEK_RISK",
                        'reason': f"GTIP {gtip_code} ({product_name}) - AB yaptırım listesinde yasaklı ürün kategorisi",
                        'found_in_sanction_list': True,
                        'prohibition_confidence': 3
                    }
                    print(f"       ⚠️  Yaptırımlı kod bulundu: {gtip_code} - {product_name}")
                else:
                    sanction_details[gtip_code] = {
                        'risk_level': "DÜŞÜK",
                        'reason': f"GTIP {gtip_code} AB yaptırım listesinde bulunamadı",
                        'found_in_sanction_list': False,
                        'prohibition_confidence': 0
                    }
            
            print(f"       ✅ AB yaptırım kontrolü tamamlandı: {len(sanctioned_found)} yüksek riskli kod")
            
        except Exception as e:
            print(f"       ❌ AB yaptırım kontrol hatası: {e}")
        
        return sanctioned_found, sanction_details

class AdvancedAIAnalyzer:
    def __init__(self):
        self.analysis_history = []
        self.sanction_analyzer = RealTimeSanctionAnalyzer()
    
    def smart_ai_analysis(self, text, company, country):
        """Gelişmiş Yerel Yapay Zeka Analizi - GTIP odaklı"""
        try:
            text_lower = text.lower()
            company_lower = company.lower()
            country_lower = country.lower()
            
            score = 0
            reasons = []
            keywords_found = []
            confidence_factors = []
            detected_products = []
            
            # GTIP kodlarını çıkar - ÖNCELİKLİ
            gtip_codes = self.sanction_analyzer.extract_gtip_codes_from_text(text)
            
            # GTIP kodları bulunduysa puanı artır
            if gtip_codes:
                score += 40
                reasons.append(f"GTIP kodları tespit edildi: {', '.join(gtip_codes)}")
                confidence_factors.append("GTIP kodları mevcut")
                print(f"       📊 GTIP kodları bulundu: {gtip_codes}")
            
            sanctioned_codes = []
            sanction_analysis = {}
            
            if gtip_codes and country.lower() in ['russia', 'rusya', 'russian']:
                sanctioned_codes, sanction_analysis = self.sanction_analyzer.check_eu_sanctions_realtime(gtip_codes)
            
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
            
            # Geliştirilmiş ticaret terimleri
            trade_indicators = {
                'export': 15, 'import': 15, 'trade': 12, 'trading': 10,
                'business': 10, 'partner': 12, 'market': 10, 'distributor': 15,
                'supplier': 12, 'dealer': 10, 'agent': 8, 'cooperation': 10,
                'collaboration': 8, 'shipment': 10, 'logistics': 8, 'customs': 8,
                'foreign': 6, 'international': 8, 'overseas': 6, 'global': 6,
                'hs code': 20, 'gtip': 20, 'harmonized system': 20, 'customs code': 15
            }
            
            for term, points in trade_indicators.items():
                if term in text_lower:
                    score += points
                    keywords_found.append(term)
                    reasons.append(f"{term} terimi bulundu")
            
            # Genişletilmiş ürün anahtar kelimeleri
            product_keywords = {
                'automotive': '8703', 'vehicle': '8703', 'car': '8703', 'motor': '8407',
                'engine': '8407', 'parts': '8708', 'component': '8708', 'truck': '8704',
                'tractor': '8701', 'trailer': '8716', 'bus': '8702', 'motorcycle': '8711',
                'computer': '8471', 'electronic': '8542', 'aircraft': '8802', 'airplane': '8802',
                'helicopter': '8802', 'weapon': '9306', 'chemical': '2844', 'signal': '8517',
                'bulldozer': '8429', 'excavator': '8429', 'generator': '8502', 'transformer': '8504',
                'battery': '8507', 'drone': '8806', 'missile': '9301', 'tank': '8710',
                'submarine': '8901', 'warship': '8906', 'radar': '8526', 'sonar': '9015',
                'optical': '9013', 'navigation': '9014', 'semiconductor': '8541',
                'integrated circuit': '8542', 'microchip': '8542', 'circuit': '8542',
                'transmission': '8517', 'reception': '8517', 'antenna': '8517', 'server': '8471',
                'router': '8517', 'switch': '8517', 'radio': '8527', 'television': '8528',
                'camera': '8525', 'lens': '9002', 'software': '8523', 'encryption': '8543',
                'cryptographic': '8543', 'security': '8543', 'bearing': '8482', 'pump': '8413',
                'valve': '8481', 'machine': '8479', 'equipment': '8479', 'tool': '8207'
            }
            
            for product, gtip in product_keywords.items():
                if product in text_lower:
                    detected_products.append(f"{product}({gtip})")
                    if gtip not in gtip_codes:
                        gtip_codes.append(gtip)
                    reasons.append(f"{product} ürün kategorisi tespit edildi (GTIP: {gtip})")
            
            # Bağlam analizi
            context_phrases = [
                f"{company_lower}.*{country_lower}",
                f"export.*{country_lower}",
                f"business.*{country_lower}",
                f"partner.*{country_lower}",
                f"market.*{country_lower}",
                f"ship.*{country_lower}",
                f"trade.*{country_lower}"
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
            
            max_possible = 250  # Puan arttığı için maksimumu yükselt
            percentage = (score / max_possible) * 100 if max_possible > 0 else 0
            
            # Risk değerlendirmesi - GTIP odaklı
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
                'AI_ANALİZ_TİPİ': 'Gelişmiş GTIP Analizi + Yaptırım Kontrolü',
                'METİN_UZUNLUĞU': word_count,
                'BENZERLİK_ORANI': f"%{percentage:.1f}",
                'YAPTIRIM_RISKI': sanctions_result['YAPTIRIM_RISKI'],
                'TESPIT_EDILEN_GTIPLER': ', '.join(gtip_codes),
                'YAPTIRIMLI_GTIPLER': ', '.join(sanctions_result['YAPTIRIMLI_GTIPLER']),
                'GTIP_ANALIZ_DETAY': sanctions_result['GTIP_ANALIZ_DETAY'],
                'AI_YAPTIRIM_UYARI': sanctions_result['AI_YAPTIRIM_UYARI'],
                'AI_TAVSIYE': sanctions_result['AI_TAVSIYE'],
                'TESPIT_EDILEN_URUNLER': ', '.join(detected_products),
                'AB_LISTESINDE_BULUNDU': sanctions_result['AB_LISTESINDE_BULUNDU']
            }
            
            self.analysis_history.append(ai_report)
            
            return ai_report
            
        except Exception as e:
            return {
                'DURUM': 'HATA',
                'HAM_PUAN': 0,
                'GÜVEN_YÜZDESİ': 0,
                'AI_AÇIKLAMA': f'AI analiz hatası: {str(e)}',
                'AI_NEDENLER': '',
                'AI_GÜVEN_FAKTÖRLERİ': '',
                'AI_ANAHTAR_KELİMELER': '',
                'AI_ANALİZ_TİPİ': 'Hata',
                'METİN_UZUNLUĞU': 0,
                'BENZERLİK_ORANI': '%0',
                'YAPTIRIM_RISKI': 'BELİRSİZ',
                'TESPIT_EDILEN_GTIPLER': '',
                'YAPTIRIMLI_GTIPLER': '',
                'GTIP_ANALIZ_DETAY': '',
                'AI_YAPTIRIM_UYARI': 'Analiz hatası',
                'AI_TAVSIYE': 'Tekrar deneyiniz',
                'TESPIT_EDILEN_URUNLER': '',
                'AB_LISTESINDE_BULUNDU': 'HAYIR'
            }
    
    def analyze_sanctions_risk(self, company, country, gtip_codes, sanctioned_codes, sanction_analysis):
        """Gelişmiş yaptırım risk analizi - GTIP odaklı"""
        analysis_result = {
            'YAPTIRIM_RISKI': 'DÜŞÜK',
            'YAPTIRIMLI_GTIPLER': [],
            'GTIP_ANALIZ_DETAY': '',
            'AI_YAPTIRIM_UYARI': '',
            'AI_TAVSIYE': '',
            'AB_LISTESINDE_BULUNDU': 'HAYIR'
        }
        
        if country.lower() in ['russia', 'rusya', 'russian'] and gtip_codes:
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
                    analysis_result['AI_TAVSIYE'] = f'⛔ BU ÜRÜNLERİN RUSYA\'YA İHRACI KESİNLİKLE YASAKTIR! GTIP: {", ".join(high_risk_codes)}. Acilen hukuki danışmanlık alın.'
                
                elif medium_risk_codes:
                    analysis_result['YAPTIRIM_RISKI'] = 'YAPTIRIMLI_ORTA_RISK'
                    analysis_result['YAPTIRIMLI_GTIPLER'] = medium_risk_codes
                    
                    details = []
                    for code in medium_risk_codes:
                        if code in sanction_analysis:
                            details.append(f"{code}: {sanction_analysis[code]['reason']}")
                    
                    analysis_result['GTIP_ANALIZ_DETAY'] = ' | '.join(details)
                    analysis_result['AI_YAPTIRIM_UYARI'] = f'🟡 ORTA YAPTIRIM RİSKİ: {company} şirketi {country} ile kısıtlamalı GTIP kodlarında ticaret yapıyor: {", ".join(medium_risk_codes)}'
                    analysis_result['AI_TAVSIYE'] = f'🟡 Bu GTIP kodları kısıtlamalı olabilir: {", ".join(medium_risk_codes)}. Resmi makamlardan teyit alınması önerilir.'
            
            else:
                analysis_result['YAPTIRIM_RISKI'] = 'DÜŞÜK'
                analysis_result['AI_YAPTIRIM_UYARI'] = f'✅ DÜŞÜK RİSK: {company} şirketinin tespit edilen GTIP kodları yaptırım listesinde değil: {", ".join(gtip_codes)}'
                analysis_result['AI_TAVSIYE'] = 'Mevcut GTIP kodları Rusya ile ticaret için uygun görünüyor. Ancak güncel yaptırım listesini düzenli kontrol edin.'
        
        elif country.lower() in ['russia', 'rusya', 'russian']:
            analysis_result['AI_YAPTIRIM_UYARI'] = 'ℹ️ GTIP kodu tespit edilemedi. Manuel kontrol önerilir.'
            analysis_result['AI_TAVSIYE'] = 'Ürün GTIP kodlarını manuel olarak kontrol edin ve AB yaptırım listesine bakın.'
        
        return analysis_result

# ... (diğer fonksiyonlar aynı, sadece yukarıdaki class'lar değişti)
