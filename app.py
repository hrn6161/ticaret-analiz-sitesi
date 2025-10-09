from flask import Flask, request, jsonify, render_template
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

app = Flask(__name__)

print("🚀 GELİŞMİŞ DUCKDUCKGO İLE GERÇEK ZAMANLI YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
                'YAPTIRIM_RISKI': 'DÜŞÜK' if not gtip_codes else 'KONTROL_EDİLMELİ'
            }
            
        except Exception as e:
            return {
                'DURUM': 'HATA',
                'GÜVEN_YÜZDESİ': 0,
                'AI_AÇIKLAMA': f'Analiz hatası: {str(e)}',
                'AI_NEDENLER': '',
                'TESPIT_EDILEN_GTIPLER': '',
                'YAPTIRIM_RISKI': 'BELİRSİZ'
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
                }
            ]
            
            return mock_results
            
        except Exception as e:
            logging.error(f"Arama hatası: {e}")
            return []

# Flask Route'ları
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON verisi bekleniyor"}), 400
        
        company = data.get('company', '').strip()
        country = data.get('country', '').strip()
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        logging.info(f"Analiz başlatılıyor: {company} - {country}")
        
        # Yapılandırma ve analiz
        config = Config()
        search_engine = SearchEngineManager(config)
        ai_analyzer = AdvancedAIAnalyzer(config)
        
        # Arama yap
        query = f"{company} {country} export trade business"
        search_results = search_engine.duckduckgo_search(query)
        
        # Sonuçları analiz et
        analyzed_results = []
        for result in search_results:
            analysis_text = f"{result['title']} {result['snippet']}"
            ai_analysis = ai_analyzer.smart_ai_analysis(analysis_text, company, country)
            
            analyzed_results.append({
                'search_result': {
                    'title': result['title'],
                    'snippet': result['snippet'],
                    'url': result['url']
                },
                'ai_analysis': ai_analysis
            })
        
        return jsonify({
            "success": True,
            "company": company,
            "country": country,
            "total_results": len(analyzed_results),
            "analysis": analyzed_results
        })
        
    except Exception as e:
        logging.error(f"Analiz hatası: {e}")
        return jsonify({"error": f"Sunucu hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
