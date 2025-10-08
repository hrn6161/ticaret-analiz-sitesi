from flask import Flask, render_template, request, send_file, jsonify
import os
import time
from analiz_kodu import run_simple_analysis, create_simple_excel_report

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
        <title>Hızlı Ticaret Analiz</title>
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
        </style>
    </head>
    <body>
        <h1>🚀 Hızlı Ticaret Analiz Sistemi</h1>
        <form id="analyzeForm">
            <div class="form-group">
                <label for="company_name">Şirket Adı:</label>
                <input type="text" id="company_name" name="company_name" value="Ford" required>
            </div>
            <div class="form-group">
                <label for="country">Ülke:</label>
                <input type="text" id="country" name="country" value="Russia" required>
            </div>
            <button type="submit">Analiz Başlat</button>
        </form>
        <div id="result"></div>
        
        <script>
            document.getElementById('analyzeForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const resultDiv = document.getElementById('result');
                
                resultDiv.innerHTML = '<div class="result">⏳ Analiz başlatılıyor...</div>';
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultDiv.innerHTML = `<div class="result success">
                            ✅ ${data.message}<br>
                            <a href="/download/${data.file_id}" style="color: #155724; font-weight: bold;">
                                📊 Excel Dosyasını İndir
                            </a>
                        </div>`;
                    } else {
                        resultDiv.innerHTML = `<div class="result error">❌ ${data.error}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result error">❌ İstek hatası: ${error}</div>`;
                }
            });
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
        
        # Hemen analiz yap
        results = run_simple_analysis(company_name, country)
        create_simple_excel_report(results, filepath)
        
        return jsonify({
            'success': True,
            'message': f'Analiz tamamlandı! {company_name} - {country}',
            'file_id': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Hata: {str(e)}'})

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return jsonify({'error': 'Dosya bulunamadı'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
