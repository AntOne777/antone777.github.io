import requests
import json
import os
import base64

MARKETS = ['en-US', 'zh-CN', 'ja-JP', 'de-DE', 'fr-FR', 'ru-RU']

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
                        # Получаем чистое имя файла из Microsoft (например, VictoriaBeach)
                        urlbase = img.get('urlbase', '')
                        img_name = urlbase.split('?id=OHR.')[-1].split('_')[0] if '?id=OHR.' in urlbase else 'Wallpaper'
                        
                        # Формируем дату для пути китайского сервера (ггггмм)
                        folder_date = f"{date[:4]}{date[4:6]}"
                        
                        # Собираем прямую ссылку на исходник, которую использует китайский сайт
                        target_url = f"https://img.nanxiongnandi.com/{folder_date}/{img_name}.jpg"
                        
                        # Кодируем целевую ссылку в Base64 для imgproxy
                        encoded_url = base64.urlsafe_b64encode(target_url.encode('utf-8')).decode('utf-8').rstrip('=')
                        
                        # Собираем финальную тяжелую ссылку на 10 МБ в максимальном качестве
                        proxy_url = f"https://imgproxy.nanxiongnandi.com/2cHFkUCWFcv3j2aRgfTrrKkRYeLGsKfw3EPwDktoC0E/w:3840/q:100/att:1/{encoded_url}.jpg"
                        
                        db[key] = {
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "market": mkt,
                            "url": proxy_url,
                            "copyright": img.get('copyright', '')
                        }
                        updated = True
        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    if updated or not db:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("База успешно переведена на супер-качество!")

if __name__ == "__main__":
    fetch_wallpapers()
