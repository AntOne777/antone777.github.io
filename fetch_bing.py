import requests
import json
import os

MARKETS = [
    'en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 
    'es-ES', 'fr-FR', 'it-IT', 'ja-JP', 'en-NZ', 'en-GB'
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
                    
                    urlbase = img.get('urlbase', '')
                    if '?id=OHR.' in urlbase:
                        raw_id = urlbase.split('?id=OHR.')[-1]
                    else:
                        raw_id = urlbase.split('/')[-1]
                    
                    clean_id = raw_id.split('_')[0]
                    key = clean_id
                    
                    if key not in db:
                        # Ссылка на тяжелый 4K UHD оригинал для скачивания/лайтбокса
                        full_uhd = "https://www.bing.com" + urlbase + "_UHD.jpg"
                        # Ссылка на легкую Full HD версию для быстрой загрузки сетки сайта
                        preview_fhd = "https://www.bing.com" + urlbase + "_1920x1080.jpg"
                        
                        db[key] = {
                            "sort_key": f"{date}_{clean_id}",
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "url": full_uhd,
                            "preview": preview_fhd,
                            "img_id": clean_id
                        }
                        updated = True
                    else:
                        current_sort = db[key].get("sort_key", "")
                        new_sort = f"{date}_{clean_id}"
                        if new_sort > current_sort:
                            db[key]["date"] = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                            db[key]["sort_key"] = new_sort
                            updated = True
        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    if updated or not db:
        db = dict(sorted(db.items(), key=lambda item: item[1].get("sort_key", ""), reverse=True))
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("База успешно обновлена: добавлены превью-ссылки!")

if __name__ == "__main__":
    fetch_wallpapers()
