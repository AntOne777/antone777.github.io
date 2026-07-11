import requests
import json
import os

MARKETS = ['en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES', 'fr-FR', 'it-IT', 'ja-JP', 'en-NZ', 'en-GB', 'nl-NL', 'pl-PL', 'pt-BR', 'pt-PT', 'ko-KR', 'ru-RU']

def fetch_wallpapers():
    db = {}
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'}

    for mkt in MARKETS:
        try:
            url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for img in r.json().get('images', []):
                    date = img.get('startdate')
                    urlbase = img.get('urlbase', '')
                    img_name = urlbase.split('/')[-1]
                    key = f"{date}_{img_name}"
                    
                    db[key] = {
                        "sort_key": f"{date}_{img_name}",
                        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                        "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                        "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                        "img_id": img_name,
                        "title": img.get('title', 'Bing'),
                        "copyright": img.get('copyright', ''),
                        "markets": [mkt]
                    }
        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    sorted_db = dict(sorted(db.items(), key=lambda i: i[1]["sort_key"], reverse=True))
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_db, f, ensure_ascii=False, indent=4)
    print("Архив обновлен.")

if __name__ == "__main__":
    fetch_wallpapers()
