from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime
import random

print("🚀 BASİT VE HIZLI ANALİZ SİSTEMİ")

def run_simple_analysis(company_name, country):
    """Basit ve hızlı analiz"""
    print(f"🎯 ANALİZ: {company_name} - {country}")
    
    results = []
    
    # Demo senaryolar
    scenarios = [
        {
            'durum': 'YÜKSEK_RİSK', 
            'güven': 85,
            'gtip': '8703, 8708',
            'açıklama': '⛔ YÜKSEK RİSK: Yasaklı otomotiv parçaları tespit edildi',
            'neden': 'GTIP 8703 ve 8708 yasaklı ürün kategorisinde'
        },
        {
            'durum': 'ORTA_RİSK',
            'güven': 60, 
            'gtip': '8471',
            'açıklama': '🟡 ORTA RİSK: Kısıtlamalı elektronik ürünler',
            'neden': 'GTIP 8471 kısıtlamalı ürün kategorisinde'
        },
        {
            'durum': 'DÜŞÜK_RİSK',
            'güven': 25,
            'gtip': '3926, 7318', 
            'açıklama': '🟢 DÜŞÜK RİSK: Serbest ticaret ürünleri',
            'neden': 'GTIP kodları yaptırım listesinde değil'
        }
    ]
    
    for i, scenario in enumerate(scenarios):
        result = {
            'ŞİRKET': company_name,
            'ÜLKE': country,
            'DURUM': scenario['durum'],
            'GÜVEN_YÜZDESİ': scenario['güven'],
            'AI_AÇIKLAMA': scenario['açıklama'],
            'AI_NEDENLER': scenario['neden'],
            'TESPIT_EDILEN_GTIPLER': scenario['gtip'],
            'YAPTIRIMLI_GTIPLER': scenario['gtip'] if scenario['durum'] == 'YÜKSEK_RİSK' else '',
            'YAPTIRIM_RISKI': 'YÜKSEK' if scenario['durum'] == 'YÜKSEK_RİSK' else 'DÜŞÜK',
            'TARİH': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'URL': f'https://example.com/{company_name.lower().replace(" ", "-")}-{i+1}',
            'BAŞLIK': f'{company_name} {country} Analiz #{i+1}'
        }
        results.append(result)
        print(f"✅ {scenario['durum']} senaryosu oluşturuldu")
    
    return results

def create_simple_excel_report(results, filename='analiz_sonuc.xlsx'):
    """Openpyxl ile basit Excel raporu"""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Analiz Sonuçları"
        
        # Başlıklar
        headers = ['ŞİRKET', 'ÜLKE', 'DURUM', 'GÜVEN_YÜZDESİ', 'AI_AÇIKLAMA', 
                  'TESPIT_EDILEN_GTIPLER', 'YAPTIRIMLI_GTIPLER', 'TARİH']
        
        # Başlık stil
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Veriler
        for row, result in enumerate(results, 2):
            ws.cell(row=row, column=1, value=result['ŞİRKET'])
            ws.cell(row=row, column=2, value=result['ÜLKE'])
            ws.cell(row=row, column=3, value=result['DURUM'])
            ws.cell(row=row, column=4, value=result['GÜVEN_YÜZDESİ'])
            ws.cell(row=row, column=5, value=result['AI_AÇIKLAMA'])
            ws.cell(row=row, column=6, value=result['TESPIT_EDILEN_GTIPLER'])
            ws.cell(row=row, column=7, value=result['YAPTIRIMLI_GTIPLER'])
            ws.cell(row=row, column=8, value=result['TARİH'])
        
        # Sütun genişlikleri
        column_widths = [20, 15, 15, 15, 50, 25, 25, 20]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width
        
        wb.save(filename)
        print(f"✅ Excel raporu oluşturuldu: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Excel hatası: {e}")
        return False

# Test
if __name__ == "__main__":
    results = run_simple_analysis("Test Şirket", "Russia")
    create_simple_excel_report(results)
    print("🎉 ANALİZ TAMAMLANDI!")
