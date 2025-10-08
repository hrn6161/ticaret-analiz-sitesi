from flask import Flask, render_template, request, send_file, jsonify
import os
import time
from analiz_kodu import run_real_analysis, create_real_excel_report
import threading

app = Flask(__name__)

UPLOAD_FOLDER = 'temp_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GERÇEK Web Araştırmalı Analiz</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, button { width: 100%; padding: 10px; margin: 5px 0; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .info { background: #d1ecf1; color: #0c5460; }
        </style>
    </head>
    <body>
        <h1>🚀 GERÇEK Web Araştırmalı Analiz Sistemi</h1>
        <p><strong>⚠️ NOT:</strong> Bu sistem gerçek web araması yapar. 2-3 dakika sürebilir.</p>
        
        <form id="analyzeForm">
            <div class="form-group">
                <label for="company_name">Şirket Adı:</label>
                <input type="text" id="company_name" name="company_name" placeholder="Ör: Ford, Toyota, BMW" required>
            </div>
            <div class="form-group">
                <label for="country">Ülke:</label>
                <input type="text" id="country" name="country" placeholder="Ör: Russia, China, Iran" required>
            </div>
            <button type="submit">🔍 GERÇEK ANALİZ BAŞLAT</button>
        </form>
        <div id="result"></div>
        
        <script>
            document.getElementById('analyzeForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const resultDiv = document.getElementById('result');
                
                resultDiv.innerHTML = '<div class="result info">🔍 GERÇEK web araştırması başlatıldı...<br>⏳ Bu işlem 2-3 dakika sürebilir.</div>';
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        if (data.ready) {
                            resultDiv.innerHTML = `<div class="result success">
                                ✅ ${data.message}<br>
                                📊 <strong>GERÇEK WEB VERİLERİYLE ANALİZ TAMAMLANDI</strong><br>
                                <a href="/download/${data.file_id}" style="color: #155724; font-weight: bold;">
                                    📥 Excel Dosyasını İndir
                                </a>
                            </div>`;
                        } else {
                            resultDiv.innerHTML = `<div class="result info">
                                ⏳ ${data.message}<br>
                                🔄 Analiz devam ediyor, lütfen bekleyin...
                            </div>`;
                            checkStatus(data.file_id);
                        }
                    } else {
                        resultDiv.innerHTML = `<div class="result error">❌ ${data.error}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result error">❌ İstek hatası: ${error}</div>`;
                }
            });
            
            function checkStatus(fileId) {
                setTimeout(async () => {
                    try {
                        const response = await fetch('/status/' + fileId);
                        const data = await response.json();
                        
                        if (data.ready) {
                            document.getElementById('result').innerHTML = 
                                `<div class="result success">
                                    ✅ ANALİZ TAMAMLANDI!<br>
                                    <a href="/download/${fileId}" style="color: #155724; font-weight: bold;">
                                        📥 Excel Dosyasını İndir
                                    </a>
                                </div>`;
                        } else {
                            checkStatus(fileId);
                        }
                    } catch (error) {
                        console.error('Status check error:', error);
                        checkStatus(fileId);
                    }
                }, 5000);
            }
        </script>
    </body>
    </html>
    """

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        company_name = request.form['company_name']
        country = request.form['country']
        
        if not company_name or not country:
            return jsonify({'error': 'Lütfen şirket adı ve ülke giriniz'})
        
        timestamp = int(time.time())
        filename = f"analiz_{timestamp}.xlsx"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Threading ile analiz başlat
        thread = threading.Thread(
            target=run_analysis_in_thread,
            args=(company_name, country, filepath)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'GERÇEK web analizi başlatıldı: {company_name} - {country}',
            'file_id': filename,
            'ready': False
        })
        
    except Exception as e:
        return jsonify({'error': f'Hata: {str(e)}'})

def run_analysis_in_thread(company_name, country, filepath):
    """Thread içinde analiz çalıştır"""
    try:
        results = run_real_analysis(company_name, country)
        create_real_excel_report(results, filepath)
        print(f"✅ ANALİZ TAMAMLANDI: {filepath}")
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=f"gercek_analiz_{file_id}",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        return jsonify({'error': 'Dosya bulunamadı'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/status/<file_id>')
def check_status(file_id):
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    return jsonify({'ready': os.path.exists(filepath)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
