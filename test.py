import requests
import json

def test_analyze():
    url = "https://your-render-app.onrender.com/analyze"
    
    data = {
        "company": "test şirket",
        "country": "test ülke"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test başarılı!")
            return True
        else:
            print("❌ Test başarısız!")
            return False
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False

if __name__ == "__main__":
    test_analyze()
