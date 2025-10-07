from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import threading
import os
import time
from analiz_kodu import run_analysis_for_company

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
        
        if not company_name or not country:
            return jsonify({'error': 'Lütfen şirket adı ve ülke giriniz'})
        
        timestamp = int(time.time())
        filename = f"analiz_sonucu_{timestamp}.xlsx"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        thread = threading.Thread(
            target=run_analysis_in_thread,
            args=(company_name, country, filepath)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'{company_name} şirketi için analiz başlatıldı. Bu işlem 5-10 dakika sürebilir.',
            'file_id': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'})

def run_analysis_in_thread(company_name, country, filepath):
    try:
        results = run_analysis_for_company(company_name, country)
        
        if results:
            df = pd.DataFrame(results)
            df.to_excel(filepath, index=False)
            print(f"✅ Analiz tamamlandı: {filepath}")
        else:
            empty_df = pd.DataFrame({'Durum': ['Analiz sonucu bulunamadı']})
            empty_df.to_excel(filepath, index=False)
            
    except Exception as e:
        print(f"Analiz hatası: {e}")
        error_df = pd.DataFrame({'Hata': [f'Analiz sırasında hata: {str(e)}']})
        error_df.to_excel(filepath, index=False)

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=f"ticaret_analizi_{file_id}",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({'error': 'Dosya bulunamadı veya henüz hazır değil'})
            
    except Exception as e:
        return jsonify({'error': f'Dosya indirme hatası: {str(e)}'})

@app.route('/status/<file_id>')
def check_status(file_id):
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    if os.path.exists(filepath):
        return jsonify({'ready': True})
    else:
        return jsonify({'ready': False})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
