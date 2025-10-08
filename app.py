from flask import Flask, render_template, request, send_file, jsonify
import threading
import os
import time
from analiz_kodu import run_fast_analysis_for_company, create_advanced_excel_report

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
            'message': f'{company_name} şirketi için HIZLI AI analiz başlatıldı. Bu işlem 2-3 dakika sürecek.',
            'file_id': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'})

def run_analysis_in_thread(company_name, country, filepath):
    try:
        print(f"🎯 HIZLI ANALİZ BAŞLATILDI: {company_name} - {country}")
        results = run_fast_analysis_for_company(company_name, country)
        
        if results:
            create_advanced_excel_report(results, filepath)
            print(f"✅ HIZLI ANALİZ TAMAMLANDI: {filepath}")
        else:
            empty_results = [{
                'ŞİRKET': company_name,
                'ÜLKE': country,
                'DURUM': 'SONUÇ_BULUNAMADI',
                'AI_AÇIKLAMA': 'Hızlı analiz sonuç bulamadı',
                'YAPTIRIM_RISKI': 'BELİRSİZ',
                'GÜVEN_YÜZDESİ': 0,
                'TARİH': time.strftime('%Y-%m-%d %H:%M')
            }]
            create_advanced_excel_report(empty_results, filepath)
            
    except Exception as e:
        print(f"Analiz hatası: {e}")
        error_results = [{
            'ŞİRKET': company_name,
            'ÜLKE': country,
            'DURUM': 'HATA',
            'AI_AÇIKLAMA': f'Analiz sırasında hata: {str(e)}',
            'YAPTIRIM_RISKI': 'BELİRSİZ',
            'GÜVEN_YÜZDESİ': 0,
            'TARİH': time.strftime('%Y-%m-%d %H:%M')
        }]
        create_advanced_excel_report(error_results, filepath)

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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
