import requests
import json
import os

# Список регионов
MARKETS = [
    'en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES', 'fr-FR', 
    'it-IT', 'ja-JP', 'en-NZ', 'en-GB', 'nl-NL', 'pl-PL', 
    'pt-BR', 'pt-PT', 'ko-KR', 'ru-RU'
]

def fetch_wallpapers():
    db = {}
    # Читаем существующий файл
    if os.path.exists('data.json') and os.path.getsize('data.json') > 0:
        with open('data.json', 'r', encoding='utf-8') as f:
            try: 
                db = json.load(f)
            except: 
                db = {}

    for mkt in MARKETS:
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                data = r.json().get('images', [])
                for img in data:
                    date = img.get('startdate')
                    urlbase = img.get('urlbase', '')
                    if not urlbase or not date: continue
                    
                    # Используем дату + уникальный ID для идентификации
                    unique_id = f"{date}_{urlbase.split('/')[-1]}"
                    
                    if unique_id not in db:
                        db[unique_id] = {
                            "sort_key": f"{date}_{urlbase.split('/')[-1]}",
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                            "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                            "img_id": urlbase.split('/')[-1].split('_')[0],
                            "title": img.get('title', 'No Title'),
                            "copyright": img.get('copyright', ''),
                            "markets": [mkt]
                        }
                    else:
                        if mkt not in db[unique_id].get("markets", []):
                            db[unique_id]["markets"].append(mkt)
        except Exception as e:
            print(f"Ошибка в {mkt}: {e}")

    # Сортировка по дате
    sorted_db = dict(sorted(db.items(), key=lambda i: i[1].get("sort_key", ""), reverse=True))
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_db, f, ensure_ascii=False, indent=4)
    
    print("Архив успешно обновлен.")

if __name__ == "__main__":
    fetch_wallpapers()
