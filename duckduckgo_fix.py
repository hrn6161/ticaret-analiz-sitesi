import requests
from bs4 import BeautifulSoup
import re

def search_duckduckgo_html(query, max_results=5):
    """DuckDuckGo HTML arayüzü ile arama yap"""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        data = {
            'q': query,
            'kl': 'us-en'
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=20)
        
        if response.status_code == 200:
            return parse_ddg_html(response.text, max_results)
        else:
            print(f"DuckDuckGo HTML hatası: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"DuckDuckGo HTML arama hatası: {e}")
        return []

def parse_ddg_html(html, max_results):
    """DuckDuckGo HTML sonuçlarını parse et"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Ana sonuçları bul
    result_elements = soup.find_all('div', class_='result')
    
    for result in result_elements[:max_results]:
        try:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')
            url_elem = result.find('a', class_='result__url')
            
            if title_elem and snippet_elem:
                title = title_elem.get_text(strip=True)
                snippet = snippet_elem.get_text(strip=True)
                url = url_elem.get('href') if url_elem else f"https://duckduckgo.com?q={title.replace(' ', '+')}"
                
                results.append({
                    'title': title,
                    'snippet': snippet,
                    'url': url
                })
        except Exception as e:
            continue
    
    return results

# Test
if __name__ == "__main__":
    test_results = search_duckduckgo_html("genel oto sanayi ve ticaret as Russia export", 3)
    print("DuckDuckGo HTML Sonuçları:")
    for i, result in enumerate(test_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet'][:100]}...")
        print(f"   {result['url']}")
        print()
