import requests
import json
import os

MARKETS = ['en-US', 'zh-CN', 'ja-JP', 'de-DE', 'fr-FR', 'ru-RU']

def get_english_meta(image_id):
    """Специальный запрос к американскому API для получения английского названия и описания"""
    try:
        # Запрашиваем данные по конкретному ID картинки у рынка en-US
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200:
            images = response.json().get('images', [])
            for img in images:
                # Если это та же самая картинка, забираем английский текст
                if image_id in img.get('urlbase', ''):
                    return img.get('title', 'Bing Wallpaper'), img.get('copyright', '')
    except Exception:
        pass
    return None, None

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
                        
                        # Выделяем уникальный ID картинки из urlbase (например, OHR.ImpalaOxpecker)
                        urlbase = img.get('urlbase', '')
                        image_id = urlbase.split('?id=')[-1].split('_')[0] if '?id=' in urlbase else urlbase.split('/')[-1]
                        
                        # По умолчанию берем то, что дал текущий регион
                        title = img.get('title', 'Bing Wallpaper')
                        copyright_text = img.get('copyright', '')
                        
                        # Если регион не американский и содержит иероглифы/заглушки, идем за английским аналогом
                        if mkt != 'en-US' or title.lower() == 'info':
                            en_title, en_copy = get_english_meta(image_id)
                            if en_title:
                                title = en_title
                            if en_copy:
                                copyright_text = en_copy

                        db[key] = {
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "market": mkt,
                            "url": base_url,
                            "title": title,
                            "copyright": copyright_text
                        }
                        updated = True
        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    if updated or not db:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("База успешно обновлена.")

if __name__ == "__main__":
    fetch_wallpapers()
