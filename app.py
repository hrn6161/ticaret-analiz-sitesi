from flask import Flask, render_template, request, send_file, jsonify
import threading
import os
import time
from analiz_kodu import run_duckduckgo_analysis, create_excel_report

app = Flask(__name__)

UPLOAD_FOLDER = 'temp_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        company_name = request.form['company_name']
        country = request.form['country']
        
        timestamp = int(time.time())
        filename = f"analiz_{timestamp}.xlsx"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        thread = threading.Thread(
            target=run_analysis_in_thread,
            args=(company_name, country, filepath)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'{company_name} için DUCKDUCKGO analizi başlatıldı (1-2 dakika)',
            'file_id': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

def run_analysis_in_thread(company_name, country, filepath):
    try:
        results = run_duckduckgo_analysis(company_name, country)
        create_excel_report(results, filepath)
        print(f"✅ ANALİZ TAMAMLANDI: {filepath}")
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")

@app.route('/download/<file_id>')
def download_file(file_id):
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Dosya bulunamadı'})

@app.route('/status/<file_id>')
def check_status(file_id):
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    return jsonify({'ready': os.path.exists(filepath)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
