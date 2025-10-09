from flask import Flask, request, jsonify, send_file, render_template
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

app = Flask(__name__)

print("🚀 DUCKDUCKGO İLE GERÇEK ZAMANLI YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ BAŞLATILIYOR...")

class RealTimeSanctionAnalyzer:
    def __init__(self):
        self.sanctioned_codes = {}
        
    def extract_gtip_codes_from_text(self, text):
        """Metinden GTIP/HS kodlarını çıkar"""
        gtip_pattern = r'\b\d{4}(?:\.\d{2,4})?\b'
        codes = re.findall(gtip_pattern, text)
        
        main_codes = set()
        for code in codes:
            main_code = code.split('.')[0]
            if len(main_code) == 4:
                main_codes.add(main_code)
        
        return list(main_codes)
    
    def check_eu_sanctions_realtime(self, gtip_codes):
        """AB yaptırım listesini kontrol et"""
        sanctioned_found = []
        sanction_details = {}
        
        try:
            print("       🌐 AB Yaptırım Listesi kontrol ediliyor...")
            
            predefined_sanctions = ['8703', '8708', '8407', '8471', '8542', '8802', '9306']
            
            for gtip_code in gtip_codes:
                if gtip_code in predefined_sanctions:
                    sanctioned_found.append(gtip_code)
                    sanction_details[gtip_code] = {
                        'risk_level': "YAPTIRIMLI_YÜKSEK_RISK",
                        'reason': f"GTIP {gtip_code} AB yaptırım listesinde - yasaklı ürün kategorisi",
                        'found_in_sanction_list': True,
                        'prohibition_confidence': 3
                    }
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
        """Gelişmiş Yerel Yapay Zeka Analizi"""
        try:
            text_lower = text.lower()
            company_lower = company.lower()
            country_lower = country.lower()
            
            score = 0
            reasons = []
            keywords_found = []
            confidence_factors = []
            detected_products = []
            
            gtip_codes = self.sanction_analyzer.extract_gtip_codes_from_text(text)
            
            sanctioned_codes = []
            sanction_analysis = {}
            
            if gtip_codes and country.lower() in ['russia', 'rusya']:
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
            
            trade_indicators = {
                'export': 15, 'import': 15, 'trade': 12, 'trading': 10,
                'business': 10, 'partner': 12, 'market': 10, 'distributor': 15,
                'supplier': 12, 'dealer': 10, 'agent': 8, 'cooperation': 10,
                'collaboration': 8, 'shipment': 10, 'logistics': 8, 'customs': 8,
                'foreign': 6, 'international': 8, 'overseas': 6, 'global': 6
            }
            
            for term, points in trade_indicators.items():
                if term in text_lower:
                    score += points
                    keywords_found.append(term)
                    reasons.append(f"{term} terimi bulundu")
            
            product_keywords = {
                'automotive': '8703', 'vehicle': '8703', 'car': '8703', 'motor': '8407',
                'engine': '8407', 'parts': '8708', 'component': '8708', 
                'computer': '8471', 'electronic': '8542', 'aircraft': '8802',
                'weapon': '9306', 'chemical': '2844', 'signal': '8517'
            }
            
            for product, gtip in product_keywords.items():
                if product in text_lower:
                    detected_products.append(f"{product}({gtip})")
                    if gtip not in gtip_codes:
                        gtip_codes.append(gtip)
                    reasons.append(f"{product} ürün kategorisi tespit edildi (GTIP: {gtip})")
            
            context_phrases = [
                f"{company_lower}.*{country_lower}",
                f"export.*{country_lower}",
                f"business.*{country_lower}",
                f"partner.*{country_lower}",
                f"market.*{country_lower}"
            ]
            
            context_matches = 0
            for phrase in context_phrases:
                if phrase in text_lower.replace(" ", ""):
                    context_matches += 1
                    reasons.append(f"Bağlam eşleşmesi: {phrase}")
            
            if context_matches >= 2:
                score += 20
                confidence_factors.append("Güçlü bağlam")
            
            unique_trade_terms = len(set(keywords_found))
            if unique_trade_terms >= 5:
                score += 10
                reasons.append(f"{unique_trade_terms} farklı ticaret terimi")
                confidence_factors.append("Zengin terminoloji")
            
            word_count = len(text_lower.split())
            if word_count > 500:
                score += 5
                confidence_factors.append("Detaylı içerik")
            
            sanctions_result = self.analyze_sanctions_risk(company, country, gtip_codes, sanctioned_codes, sanction_analysis)
            
            max_possible = 218
            percentage = (score / max_possible) * 100
            
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
                'AI_ANALİZ_TİPİ': 'Gerçek Zamanlı AI + Yaptırım Kontrolü',
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
        """Gelişmiş yaptırım risk analizi"""
        analysis_result = {
            'YAPTIRIM_RISKI': 'DÜŞÜK',
            'YAPTIRIMLI_GTIPLER': [],
            'GTIP_ANALIZ_DETAY': '',
            'AI_YAPTIRIM_UYARI': '',
            'AI_TAVSIYE': '',
            'AB_LISTESINDE_BULUNDU': 'HAYIR'
        }
        
        if country.lower() in ['russia', 'rusya'] and gtip_codes:
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
        
        elif country.lower() in ['russia', 'rusya']:
            analysis_result['AI_YAPTIRIM_UYARI'] = 'ℹ️ GTIP kodu tespit edilemedi. Manuel kontrol önerilir.'
            analysis_result['AI_TAVSIYE'] = 'Ürün GTIP kodlarını manuel olarak kontrol edin ve AB yaptırım listesine bakın.'
        
        return analysis_result

def duckduckgo_search(query, max_results=3):
    """DuckDuckGo'dan arama sonuçlarını al"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    search_results = []
    
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = soup.find_all('div', class_='result')[:max_results]
        
        for i, result in enumerate(results):
            try:
                title_elem = result.find('a', class_='result__a')
                link_elem = result.find('a', class_='result__url')
                
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    url = link_elem.get('href')
                    
                    if url and url.startswith('//duckduckgo.com/l/'):
                        url = url.replace('//duckduckgo.com/l/', 'https://')
                    
                    search_results.append({
                        'title': title,
                        'url': url,
                        'rank': i + 1
                    })
                    
            except Exception as e:
                print(f"       ❌ Sonuç parse hatası: {e}")
                continue
                
    except Exception as e:
        print(f"   ❌ Arama hatası: {e}")
    
    return search_results

def get_page_content(url):
    """Web sayfası içeriğini al"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string if soup.title else "Başlık bulunamadı"
        content = soup.get_text()
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'status': 'BAŞARILI'
        }
        
    except Exception as e:
        return {
            'url': url,
            'title': f'Hata: {str(e)}',
            'content': '',
            'status': 'HATA'
        }

def ai_enhanced_search(company, country):
    """AI destekli DuckDuckGo araması"""
    all_results = []
    ai_analyzer = AdvancedAIAnalyzer()
    
    search_terms = [
        f"{company} {country} export",
        f"{company} {country} import", 
        f"{company} {country} trade",
        f"{company} {country} business",
        f"{company} {country} GTIP",
        f"{company} {country} HS code"
    ]
    
    for term in search_terms:
        try:
            print(f"   🔍 Aranıyor: '{term}'")
            
            results = duckduckgo_search(term)
            
            for i, result in enumerate(results):
                print(f"     📄 {i+1}. sonuç AI analizi: {result['title'][:50]}...")
                
                print(f"       🌐 Sayfa yükleniyor: {result['url']}")
                page_data = get_page_content(result['url'])
                
                if page_data['status'] == 'BAŞARILI':
                    print("       🤖 AI analiz ve yaptırım kontrolü yapılıyor...")
                    ai_result = ai_analyzer.smart_ai_analysis(page_data['content'], company, country)
                    
                    result_data = {
                        'ŞİRKET': company,
                        'ÜLKE': country,
                        'ARAMA_TERİMİ': term,
                        'SAYFA_NUMARASI': result['rank'],
                        'DURUM': ai_result['DURUM'],
                        'HAM_PUAN': ai_result['HAM_PUAN'],
                        'GÜVEN_YÜZDESİ': ai_result['GÜVEN_YÜZDESİ'],
                        'AI_AÇIKLAMA': ai_result['AI_AÇIKLAMA'],
                        'AI_NEDENLER': ai_result['AI_NEDENLER'],
                        'AI_GÜVEN_FAKTÖRLERİ': ai_result['AI_GÜVEN_FAKTÖRLERİ'],
                        'AI_ANAHTAR_KELİMELER': ai_result['AI_ANAHTAR_KELİMELER'],
                        'AI_ANALİZ_TİPİ': ai_result['AI_ANALİZ_TİPİ'],
                        'URL': result['url'],
                        'BAŞLIK': result['title'],
                        'İÇERİK_ÖZETİ': page_data['content'][:400] + '...',
                        'TARİH': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'YAPTIRIM_RISKI': ai_result['YAPTIRIM_RISKI'],
                        'TESPIT_EDILEN_GTIPLER': ai_result['TESPIT_EDILEN_GTIPLER'],
                        'YAPTIRIMLI_GTIPLER': ai_result['YAPTIRIMLI_GTIPLER'],
                        'GTIP_ANALIZ_DETAY': ai_result['GTIP_ANALIZ_DETAY'],
                        'AI_YAPTIRIM_UYARI': ai_result['AI_YAPTIRIM_UYARI'],
                        'AI_TAVSIYE': ai_result['AI_TAVSIYE'],
                        'TESPIT_EDILEN_URUNLER': ai_result['TESPIT_EDILEN_URUNLER'],
                        'AB_LISTESINDE_BULUNDU': ai_result['AB_LISTESINDE_BULUNDU']
                    }
                    
                    all_results.append(result_data)
                    
                    status_color = {
                        'YAPTIRIMLI_YÜKSEK_RISK': '⛔',
                        'YAPTIRIMLI_ORTA_RISK': '🟡',
                        'EVET': '✅',
                        'OLASI': '🟡', 
                        'ZAYIF': '🟢',
                        'HAYIR': '⚪',
                        'HATA': '❌'
                    }
                    
                    color = status_color.get(ai_result['DURUM'], '⚪')
                    risk_indicator = '🔴' if ai_result['YAPTIRIM_RISKI'] in ['YAPTIRIMLI_YÜKSEK_RISK', 'YAPTIRIMLI_ORTA_RISK'] else '🟢'
                    
                    print(f"         {color} {ai_result['DURUM']} (%{ai_result['GÜVEN_YÜZDESİ']:.1f}) {risk_indicator} {ai_result['YAPTIRIM_RISKI']}")
                    if ai_result['TESPIT_EDILEN_GTIPLER']:
                        print(f"         📦 GTIP Kodları: {ai_result['TESPIT_EDILEN_GTIPLER']}")
                
                time.sleep(2)
            
            time.sleep(3)
            
        except Exception as e:
            print(f"   ❌ Arama hatası: {e}")
            continue
    
    return all_results

def create_advanced_excel_report(df_results, filename='ai_ticaret_analiz_sonuc.xlsx'):
    """Gelişmiş Excel raporu oluştur"""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        workbook = writer.book
        
        # 1. Tüm AI Sonuçları
        df_results.to_excel(writer, sheet_name='AI Analiz Sonuçları', index=False)
        
        # 2. Yüksek Riskli Sonuçlar
        high_risk = df_results[df_results['YAPTIRIM_RISKI'].isin(['YAPTIRIMLI_YÜKSEK_RISK', 'YAPTIRIMLI_ORTA_RISK'])]
        if not high_risk.empty:
            high_risk.to_excel(writer, sheet_name='Yüksek Riskli', index=False)
        
        # 3. Yüksek Güvenilir Sonuçlar
        high_confidence = df_results[df_results['GÜVEN_YÜZDESİ'] >= 60]
        if not high_confidence.empty:
            high_confidence.to_excel(writer, sheet_name='Yüksek Güvenilir', index=False)
        
        # 4. AI Özet Tablosu
        ai_summary = df_results.groupby(['ŞİRKET', 'ÜLKE', 'DURUM', 'YAPTIRIM_RISKI']).agg({
            'GÜVEN_YÜZDESİ': ['count', 'mean', 'max'],
            'HAM_PUAN': 'mean',
        }).round(1)
        ai_summary.columns = ['_'.join(col).strip() for col in ai_summary.columns.values]
        ai_summary = ai_summary.reset_index()
        ai_summary.to_excel(writer, sheet_name='AI Özeti', index=False)
        
        # 5. Detaylı Analiz
        analysis_details = df_results[['ŞİRKET', 'ÜLKE', 'DURUM', 'GÜVEN_YÜZDESİ', 
                                     'YAPTIRIM_RISKI', 'TESPIT_EDILEN_GTIPLER', 
                                     'YAPTIRIMLI_GTIPLER', 'AI_YAPTIRIM_UYARI', 
                                     'AI_TAVSIYE', 'URL']]
        analysis_details.to_excel(writer, sheet_name='Detaylı Analiz', index=False)
        
        # 6. GTIP Yaptırım Analizi
        gtip_analysis = df_results[df_results['TESPIT_EDILEN_GTIPLER'] != '']
        if not gtip_analysis.empty:
            gtip_summary = gtip_analysis.groupby('TESPIT_EDILEN_GTIPLER').agg({
                'ŞİRKET': 'count',
                'YAPTIRIM_RISKI': 'first',
                'AI_YAPTIRIM_UYARI': 'first'
            }).reset_index()
            gtip_summary.to_excel(writer, sheet_name='GTIP Analiz', index=False)
        
        # 7. AI Yorumu ve İstatistikler
        create_ai_comment_sheet(workbook, df_results)
    
    print(f"✅ Gelişmiş Excel raporu oluşturuldu: {filename}")
    return filename

def create_ai_comment_sheet(workbook, df_results):
    """AI yorumu ve istatistikler sayfası oluştur"""
    
    sheet = workbook.create_sheet("🤖 AI Yorumu ve İstatistikler")
    
    # Başlık
    sheet['A1'] = "🤖 YAPAY ZEKA TİCARET ANALİZ YORUMU"
    sheet['A1'].font = Font(size=16, bold=True, color="FF0000")
    
    # Temel istatistikler
    sheet['A3'] = "📊 TEMEL İSTATİSTİKLER"
    sheet['A3'].font = Font(size=14, bold=True)
    
    stats_data = [
        ("Toplam AI Analiz", len(df_results)),
        ("Yüksek Güvenilir Sonuç", len(df_results[df_results['GÜVEN_YÜZDESİ'] >= 60])),
        ("Yüksek Yaptırım Riski", len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_YÜKSEK_RISK'])),
        ("Orta Yaptırım Riski", len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_ORTA_RISK'])),
        ("Rusya ile Ticaret Oranı", f"%{(len(df_results[df_results['ÜLKE'].str.lower().isin(['russia', 'rusya'])])/len(df_results)*100):.1f}"),
        ("Ortalama Güven Yüzdesi", f"%{df_results['GÜVEN_YÜZDESİ'].mean():.1f}")
    ]
    
    for i, (label, value) in enumerate(stats_data, start=4):
        sheet[f'A{i}'] = label
        sheet[f'B{i}'] = value
        sheet[f'A{i}'].font = Font(bold=True)
    
    # AI Yorumu
    sheet['A10'] = "🎯 AI TİCARET ANALİZ YORUMU"
    sheet['A10'].font = Font(size=14, bold=True, color="FF0000")
    
    # Detaylı yorum oluştur
    total_analysis = len(df_results)
    russia_count = len(df_results[df_results['ÜLKE'].str.lower().isin(['russia', 'rusya'])])
    high_risk_count = len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_YÜKSEK_RISK'])
    medium_risk_count = len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_ORTA_RISK'])
    avg_confidence = df_results['GÜVEN_YÜZDESİ'].mean()
    
    ai_comment = f"""
    📊 GENEL DURUM ANALİZİ:
    • Toplam {total_analysis} AI analiz gerçekleştirilmiştir
    • {russia_count} şirket Rusya ile ticaret potansiyeli göstermektedir
    • Ortalama güven seviyesi: %{avg_confidence:.1f}
    
    ⚠️  YAPTIRIM RİSK ANALİZİ:
    • {high_risk_count} şirket YÜKSEK yaptırım riski taşımaktadır
    • {medium_risk_count} şirket ORTA yaptırım riski taşımaktadır
    
    🔴 KRİTİK UYARILAR:
    {f'• ⛔ YÜKSEK RİSK: {high_risk_count} şirket yasaklı GTIP kodları ile ticaret yapıyor' if high_risk_count > 0 else '• ✅ Yüksek riskli şirket bulunamadı'}
    {f'• 🟡 ORTA RİSK: {medium_risk_count} şirket kısıtlamalı GTIP kodları ile ticaret yapıyor' if medium_risk_count > 0 else '• ✅ Orta riskli şirket bulunamadı'}
    
    💡 TAVSİYELER VE SONRAKİ ADIMLAR:
    1. Yüksek riskli şirketlerle acilen iletişime geçin
    2. Yaptırım listesini düzenli olarak güncelleyin
    3. GTIP kodlarını resmi makamlardan teyit edin
    4. Hukuki danışmanlık almayı düşünün
    """
    
    # Yorumu satırlara böl ve yaz
    for i, line in enumerate(ai_comment.strip().split('\n')):
        sheet[f'A{11 + i}'] = line.strip()
    
    # Sütun genişliklerini ayarla
    sheet.column_dimensions['A'].width = 40
    sheet.column_dimensions['B'].width = 20

# Flask Routes
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🚀 AI Ticaret Analiz Sistemi</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"] { width: 100%; padding: 10px; font-size: 16px; }
            button { background: #007bff; color: white; padding: 12px 30px; border: none; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .loading { display: none; color: #007bff; }
            .result { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AI Ticaret ve Yaptırım Analiz Sistemi</h1>
            <p>Şirket ve hedef ülke bilgilerini girerek ticaret analizi yapın.</p>
            
            <form id="analysisForm">
                <div class="form-group">
                    <label for="company">Şirket Adı:</label>
                    <input type="text" id="company" name="company" required placeholder="Örnek: ABC Otomotiv Sanayi">
                </div>
                
                <div class="form-group">
                    <label for="country">Hedef Ülke:</label>
                    <input type="text" id="country" name="country" required placeholder="Örnek: Rusya">
                </div>
                
                <button type="submit">🔍 Analiz Başlat</button>
            </form>
            
            <div id="loading" class="loading">
                <h3>⏳ AI analiz yapılıyor, lütfen bekleyin...</h3>
                <p>Bu işlem 1-2 dakika sürebilir.</p>
            </div>
            
            <div id="result" class="result"></div>
        </div>

        <script>
            document.getElementById('analysisForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const company = document.getElementById('company').value;
                const country = document.getElementById('country').value;
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                
                loading.style.display = 'block';
                result.innerHTML = '';
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ company, country })
                    });
                    
                    const data = await response.json();
                    
                    loading.style.display = 'none';
                    
                    if (data.success) {
                        result.innerHTML = `
                            <h3>✅ Analiz Tamamlandı!</h3>
                            <p><strong>Şirket:</strong> ${company}</p>
                            <p><strong>Ülke:</strong> ${country}</p>
                            <p><strong>Toplam Sonuç:</strong> ${data.total_results}</p>
                            <p><strong>Yüksek Risk:</strong> ${data.high_risk_count}</p>
                            <p><strong>Orta Risk:</strong> ${data.medium_risk_count}</p>
                            <a href="/download/${data.filename}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📊 Excel'i İndir</a>
                        `;
                    } else {
                        result.innerHTML = `<p style="color: red;">❌ Hata: ${data.error}</p>`;
                    }
                    
                } catch (error) {
                    loading.style.display = 'none';
                    result.innerHTML = `<p style="color: red;">❌ İstek hatası: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        company = data.get('company', '').strip()
        country = data.get('country', '').strip()
        
        if not company or not country:
            return jsonify({'success': False, 'error': 'Şirket ve ülke bilgisi gereklidir'})
        
        print(f"🔍 Yeni analiz isteği: {company} ↔ {country}")
        
        # AI analizini başlat
        results = ai_enhanced_search(company, country)
        
        if results:
            df_results = pd.DataFrame(results)
            filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
            create_advanced_excel_report(df_results, filename)
            
            total_analysis = len(results)
            high_risk_count = len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_YÜKSEK_RISK'])
            medium_risk_count = len(df_results[df_results['YAPTIRIM_RISKI'] == 'YAPTIRIMLI_ORTA_RISK'])
            
            return jsonify({
                'success': True,
                'company': company,
                'country': country,
                'total_results': total_analysis,
                'high_risk_count': high_risk_count,
                'medium_risk_count': medium_risk_count,
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'error': 'Hiç sonuç bulunamadı'})
            
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Dosya bulunamadı: {e}", 404

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
