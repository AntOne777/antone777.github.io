import requests
import json
import os
import logging
from typing import Dict, Any

# Настройка логирования для удобного отслеживания в логах GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

MARKETS = [
    'en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES', 'fr-FR', 'it-IT', 
    'ja-JP', 'en-NZ', 'en-GB', 'nl-NL', 'pl-PL', 'pt-BR', 'pt-PT', 'ko-KR', 'ru-RU'
]

DATA_FILE = 'data.json'

def fetch_wallpapers() -> None:
    db: Dict[str, Any] = {}
    
    # Безопасная загрузка базы
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Ошибка чтения {DATA_FILE}: {e}. Начинаем с пустого архива.")
            db = {}

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/127.0.0.0 Safari/537.36'}

    for mkt in MARKETS:
        try:
            url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=5&mkt={mkt}"
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status() # Проверка статуса ответа
            
            data = r.json()
            for img in data.get('images', []):
                urlbase = img.get('urlbase', '')
                # Безопасное извлечение ID
                raw_id = urlbase.split('?id=OHR.')[-1] if '?id=OHR.' in urlbase else urlbase.split('/')[-1]
                clean_id = raw_id.split('_')[0]
                date = img.get('startdate', '')
                copyright_text = img.get('copyright', '')

                if clean_id not in db:
                    db[clean_id] = {
                        "sort_key": f"{date}_{clean_id}",
                        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                        "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                        "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                        "img_id": clean_id,
                        "title": img.get('title', clean_id),
                        "description": copyright_text,
                        "copyright": copyright_text,
                        "markets": [mkt]
                    }
                else:
                    # Дополняем данные
                    if not db[clean_id].get("description") and copyright_text:
                        db[clean_id]["description"] = copyright_text
                    
                    if mkt not in db[clean_id].get("markets", []):
                        db[clean_id]["markets"].append(mkt)
                        
        except Exception as e:
            logging.warning(f"Ошибка при запросе рынка {mkt}: {e}")

    # Сортировка: новые сверху
    sorted_db = dict(sorted(db.items(), key=lambda i: i[1]["sort_key"], reverse=True))
    
    # Сохранение с проверкой записи
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_db, f, ensure_ascii=False, indent=4)
        logging.info(f"Архив успешно обновлен. Записей: {len(sorted_db)}")
    except IOError as e:
        logging.error(f"Не удалось записать файл: {e}")

if __name__ == "__main__":
    fetch_wallpapers()
