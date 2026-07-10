import requests
import json
import os

# Полный список из 11 стран по вашему запросу
MARKETS = [
    'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES', 
    'fr-FR', 'it-IT', 'ja-JP', 'en-NZ', 'en-GB', 'en-US'
]

def fetch_wallpapers():
    if os.path.exists('data.json') and os.path.getsize('data.json') > 0:
        with open('data.json', 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except json.JSONDecodeError: db = {}
    else:
        db = {}

    updated = False

    for mkt in MARKETS:
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                images = response.json().get('images', [])
                
                for img in images:
                    date = img.get('startdate')
                    if not date: continue
                    
                    key = f"{date}_{mkt}"
                    
                    if key not in db:
                        base_url = "https://www.bing.com" + img['urlbase'] + "_UHD.jpg"
                        
                        db[key] = {
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "market": mkt,
                            "url": base_url,
                            "copyright": img.get('copyright', '')
                        }
                        updated = True
        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    if updated or not db:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("База успешно обновлена для 11 стран!")

if __name__ == "__main__":
    fetch_wallpapers()
