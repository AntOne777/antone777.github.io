import requests
import json
import os
import re

MARKETS = ['en-US', 'zh-CN', 'ja-JP', 'de-DE', 'fr-FR', 'ru-RU']

def clean_to_english_title(copyright_text, default_title):
    if not copyright_text:
        return default_title
    
    # Ищем текст внутри скобок после знака © (например, © Author/Getty Images)
    match = re.search(r'\(©\s*([^)]+)\)', copyright_text)
    if match:
        credits = match.group(1).strip()
        # Убираем "/Getty Images", если хотим сделать заголовок короче и чище
        clean_title = credits.split('/')[0].strip()
        return clean_title
        
    return default_title

def fetch_wallpapers():
    if os.path.exists('data.json') and os.path.getsize('data.json') > 0:
        with open('data.json', 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = {}
    else:
        db = {}

    updated = False

    for mkt in MARKETS:
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                
                for img in images:
                    date = img.get('startdate')
                    if not date:
                        continue
                    
                    key = f"{date}_{mkt}"
                    
                    if key not in db:
                        base_url = "https://www.bing.com" + img['urlbase'] + "_UHD.jpg"
                        
                        raw_copyright = img.get('copyright', '')
                        raw_title = img.get('title', 'Bing Wallpaper')
                        
                        # Извлекаем красивый английский заголовок вместо иероглифов
                        english_title = clean_to_english_title(raw_copyright, raw_title)
                        
                        db[key] = {
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "market": mkt,
                            "url": base_url,
                            "title": english_title,
                            "copyright": raw_copyright
                        }
                        updated = True
        except Exception as e:
            print(f"Ошибка для региона {mkt}: {e}")

    if updated or not db:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("База данных успешно обновлена.")

if __name__ == "__main__":
    fetch_wallpapers()
