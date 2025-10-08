import pandas as pd
import random
from datetime import datetime

print("🚀 DEMO MODU - ANINDA ÇALIŞAN ANALİZ SİSTEMİ")

def run_demo_analysis(company_name, country):
    """ANINDA çalışan demo analiz"""
    print(f"🎯 DEMO ANALİZ: {company_name} - {country}")
    
    results = []
    scenarios = [
        {'status': 'YÜKSEK_RİSK', 'confidence': 85, 'gtip': ['8703', '8708'], 'reason': 'Yasaklı otomotiv parçaları'},
        {'status': 'ORTA_RİSK', 'confidence': 60, 'gtip': ['8471'], 'reason': 'Kısıtlamalı elektronik ürünler'},
        {'status': 'DÜŞÜK_RİSK', 'confidence': 30, 'gtip': ['3926', '7318'], 'reason': 'Serbest ticaret ürünleri'}
    ]
    
    for i, scenario in enumerate(scenarios):
        result = {
            'ŞİRKET': company_name, 'ÜLKE': country,
            'DURUM': scenario['status'], 'GÜVEN_YÜZDESİ': scenario['confidence'],
            'AI_AÇIKLAMA': f"{scenario['status']}: {company_name} - {country} (%{scenario['confidence']})",
            'AI_NEDENLER': f"Demo {i+1} - {scenario['reason']}",
            'YAPTIRIM_RISKI': 'YÜKSEK_RİSK' if scenario['status'] == 'YÜKSEK_RİSK' else 'DÜŞÜK',
            'TESPIT_EDILEN_GTIPLER': ', '.join(scenario['gtip']),
            'YAPTIRIMLI_GTIPLER': ', '.join(scenario['gtip']) if scenario['status'] == 'YÜKSEK_RİSK' else '',
            'TARİH': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        results.append(result)
    
    print(f"✅ DEMO ANALİZ TAMAMLANDI: {len(results)} sonuç")
    return results

def create_demo_excel_report(results, filename='demo_analiz.xlsx'):
    try:
        df = pd.DataFrame(results)
        df.to_excel(filename, index=False)
        print(f"✅ DEMO Excel oluşturuldu: {filename}")
        return True
    except Exception as e:
        print(f"❌ Excel hatası: {e}")
        return False
