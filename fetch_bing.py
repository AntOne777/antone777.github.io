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

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/127.0.0.0 Safari/537.36'}

    for mkt in MARKETS:
        try:
            url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                for img in r.json().get('images', []):
                    # Извлекаем чистый ID картинки (без региональных суффиксов)
                    urlbase = img.get('urlbase', '')
                    raw_id = urlbase.split('?id=OHR.')[-1] if '?id=OHR.' in urlbase else urlbase.split('/')[-1]
                    clean_id = raw_id.split('_')[0]
                    
                    date = img.get('startdate')

                    # Если картинки еще нет в базе — создаем запись
                    if clean_id not in db:
                        db[clean_id] = {
                            "sort_key": f"{date}_{clean_id}",
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                            "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                            "img_id": clean_id,
                            "title": img.get('title', 'Bing Wallpaper'),
                            "copyright": img.get('copyright', ''),
                            "markets": [mkt]
                        }
                    else:
                        # Если картинка есть — просто добавляем рынок, если его еще нет
                        if mkt not in db[clean_id].get("markets", []):
                            db[clean_id]["markets"].append(mkt)
        except Exception as e:
            print(f"Ошибка в {mkt}: {e}")

    # Сортируем по sort_key (дате)
    sorted_db = dict(sorted(db.items(), key=lambda i: i[1]["sort_key"], reverse=True))
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_db, f, ensure_ascii=False, indent=4)
    print("Архив успешно дедуплицирован и обновлен.")

if __name__ == "__main__":
    fetch_wallpapers()
