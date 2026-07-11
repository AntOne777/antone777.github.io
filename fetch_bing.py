import requests
import json
import os

MARKETS = ['en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES', 'fr-FR', 'it-IT', 'ja-JP', 'en-NZ', 'en-GB', 'nl-NL', 'pl-PL', 'pt-BR', 'pt-PT', 'ko-KR', 'ru-RU']

def fetch_wallpapers():
    # Загружаем текущую базу
    db = {}
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    for mkt in MARKETS:
        try:
            url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=3&mkt={mkt}"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                for img in r.json().get('images', []):
                    # Ключ теперь строго дата + имя файла без лишнего
                    date = img.get('startdate')
                    urlbase = img.get('urlbase', '')
                    img_name = urlbase.split('/')[-1]
                    key = f"{date}_{img_name}"
                    
                    if key not in db:
                        db[key] = {
                            "sort_key": f"{date}_{img_name}",
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                            "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                            "img_id": img_name,
                            "title": img.get('title', 'Bing Wallpaper'),
                            "copyright": img.get('copyright', ''),
                            "markets": [mkt]
                        }
                    else:
                        if mkt not in db[key].get("markets", []):
                            db[key]["markets"].append(mkt)
        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    # Сортируем и сохраняем
    sorted_db = dict(sorted(db.items(), key=lambda i: i[1]["sort_key"], reverse=True))
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_db, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_wallpapers()
