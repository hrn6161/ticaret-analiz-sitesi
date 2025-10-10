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

print("🚀 GELİŞMİŞ YAPAY ZEKA YAPTIRIM ANALİZ SİSTEMİ BAŞLATILIYOR...")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        self.MAX_RESULTS = 3  # Azaltıldı: 5'ten 3'e
        self.REQUEST_TIMEOUT = 15  # Azaltıldı: 20'den 15'e
        self.RETRY_ATTEMPTS = 2  # Azaltıldı: 3'ten 2'ye
        self.DELAY_BETWEEN_REQUESTS = 2.0  # Azaltıldı: 3.0'dan 2.0'a
        self.DELAY_BETWEEN_SEARCHES = 2.0  # Azaltıldı: 5.0'dan 2.0'a
        self.EU_SANCTIONS_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02014R0833-20250720"
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

# EUSanctionsAPI, RealTimeSanctionAnalyzer, SearchEngineManager, AdvancedAIAnalyzer, AdvancedTradeAnalyzer sınıfları aynı kalacak
# (Önceki dosyadan kopyala, burada uzunluk nedeniyle kısaltıyorum)

class EUSanctionsAPI:
    # ... (Önceki dosyadan aynen al)
    pass

class RealTimeSanctionAnalyzer:
    # ... (Önceki dosyadan aynen al)
    pass

class SearchEngineManager:
    # ... (Önceki dosyadan aynen al)
    pass

class AdvancedAIAnalyzer:
    # ... (Önceki dosyadan aynen al)
    pass

class AdvancedTradeAnalyzer:
    # ... (Önceki dosyadan aynen al)
    pass

def create_advanced_excel_report(results, company, country):
    # ... (Önceki dosyadan aynen al)
    pass

# Flask Route'ları - GÜNCELLENDİ
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # CORS headers ekle
        response_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        # OPTIONS isteği için handling
        if request.method == 'OPTIONS':
            return '', 200, response_headers
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON verisi bekleniyor"}), 400, response_headers
        
        company = data.get('company', '').strip()
        country = data.get('country', '').strip()
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400, response_headers
        
        logging.info(f"Analiz başlatılıyor: {company} - {country}")
        
        # Yapılandırma ve analiz
        config = Config()
        analyzer = AdvancedTradeAnalyzer(config)
        
        # Arama yap (timeout süresi ile)
        try:
            results = analyzer.ai_enhanced_search(company, country)
        except Exception as search_error:
            logging.error(f"Arama hatası: {search_error}")
            return jsonify({"error": f"Arama işlemi sırasında hata: {str(search_error)}"}), 500, response_headers
        
        # Excel raporu oluştur
        excel_filepath = create_advanced_excel_report(results, company, country)
        
        response_data = {
            "success": True,
            "company": company,
            "country": country,
            "total_results": len(results),
            "analysis": results,
            "excel_download_url": f"/download-excel?company={company}&country={country}" if excel_filepath else None
        }
        
        return jsonify(response_data), 200, response_headers
        
    except Exception as e:
        logging.error(f"Analiz hatası: {e}")
        return jsonify({"error": f"Sunucu hatası: {str(e)}"}), 500, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

@app.route('/download-excel')
def download_excel():
    try:
        company = request.args.get('company', '')
        country = request.args.get('country', '')
        
        if not company or not country:
            return jsonify({"error": "Şirket ve ülke bilgisi gereklidir"}), 400
        
        filename = f"{company.replace(' ', '_')}_{country}_analiz.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({"error": "Excel dosyası bulunamadı"}), 404
            
    except Exception as e:
        logging.error(f"Excel indirme hatası: {e}")
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "Ticaret Analiz Sistemi"
    })

# Hata yönetimi
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Sayfa bulunamadı"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Sunucu iç hatası"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"İşlenmeyen hata: {e}")
    return jsonify({"error": "Beklenmeyen sunucu hatası"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
