import requests
import json
import os

MARKETS = ['en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES', 'fr-FR', 'it-IT', 'ja-JP', 'en-NZ', 'en-GB']

def fetch_wallpapers():
    db = {}
    if os.path.exists('data.json') and os.path.getsize('data.json') > 0:
        with open('data.json', 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    updated = False
    for mkt in MARKETS:
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                for img in r.json().get('images', []):
                    date, urlbase = img.get('startdate'), img.get('urlbase', '')
                    if not urlbase: continue
                    
                    raw_id = urlbase.split('?id=OHR.')[-1] if '?id=OHR.' in urlbase else urlbase.split('/')[-1]
                    clean_id = raw_id.split('_')[0]
                    
                    if clean_id not in db:
                        db[clean_id] = {
                            "sort_key": f"{date}_{clean_id}",
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                            "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                            "img_id": clean_id,
                            "title": img.get('title', clean_id),
                            "copyright": img.get('copyright', ''),
                            "markets": [mkt]
                        }
                        updated = True
                    else:
                        item = db[clean_id]
                        # Обновление статистики и миграция полей
                        if mkt not in item.get("markets", []):
                            item.setdefault("markets", []).append(mkt)
                            updated = True
                        for field in ["preview", "title", "copyright"]:
                            if field not in item:
                                item[field] = img.get(field, '') if field != "preview" else f"https://www.bing.com{urlbase}_1920x1080.jpg"
                                updated = True
                        
                        new_sort = f"{date}_{clean_id}"
                        if new_sort > item.get("sort_key", ""):
                            item["sort_key"] = new_sort
                            item["date"] = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                            updated = True
        except Exception as e:
            print(f"Ошибка в {mkt}: {e}")

    if updated:
        db = dict(sorted(db.items(), key=lambda i: i[1].get("sort_key", ""), reverse=True))
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_wallpapers()
