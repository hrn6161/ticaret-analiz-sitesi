from flask import Flask, render_template, request, send_file, jsonify
import threading
import os
import time
from analiz_kodu import run_analysis_for_company
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import io

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
            'message': f'{company_name} şirketi için analiz başlatıldı. Bu işlem birkaç saniye sürebilir.',
            'file_id': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'})

def run_analysis_in_thread(company_name, country, filepath):
    try:
        results = run_analysis_for_company(company_name, country)
        
        if results:
            # Pandas olmadan Excel oluştur
            wb = Workbook()
            ws = wb.active
            ws.title = "Analiz Sonuçları"
            
            # Başlıklar
            headers = list(results[0].keys())
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
                ws.cell(row=1, column=col).font = Font(bold=True)
            
            # Veriler
            for row, result in enumerate(results, 2):
                for col, key in enumerate(headers, 1):
                    ws.cell(row=row, column=col, value=result[key])
            
            wb.save(filepath)
            print(f"✅ Analiz tamamlandı: {filepath}")
        else:
            # Boş Excel oluştur
            wb = Workbook()
            ws = wb.active
            ws['A1'] = 'Durum'
            ws['A2'] = 'Analiz sonucu bulunamadı'
            wb.save(filepath)
            
    except Exception as e:
        print(f"Analiz hatası: {e}")
        # Hata Excel'i oluştur
        wb = Workbook()
        ws = wb.active
        ws['A1'] = 'Hata'
        ws['A2'] = f'Analiz sırasında hata: {str(e)}'
        wb.save(filepath)

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
