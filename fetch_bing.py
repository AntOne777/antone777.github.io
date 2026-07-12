import requests
import json
import os


MARKETS = [
    'en-US', 'en-AU', 'en-CA', 'zh-CN', 'de-DE', 'es-ES',
    'fr-FR', 'it-IT', 'ja-JP', 'en-NZ', 'en-GB', 'nl-NL',
    'pl-PL', 'pt-BR', 'pt-PT', 'ko-KR', 'ru-RU'
]


def fetch_wallpapers():
    # Загружаем базу
    db = {}

    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
            except:
                db = {}

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'Chrome/127.0.0.0 Safari/537.36'
        )
    }

    for mkt in MARKETS:
        try:
            url = (
                f"https://www.bing.com/HPImageArchive.aspx?"
                f"format=js&idx=0&n=5&mkt={mkt}"
            )

            r = requests.get(url, headers=headers, timeout=15)

            if r.status_code == 200:
                for img in r.json().get('images', []):
                    urlbase = img.get('urlbase', '')

                    raw_id = (
                        urlbase.split('?id=OHR.')[-1]
                        if '?id=OHR.' in urlbase
                        else urlbase.split('/')[-1]
                    )

                    clean_id = raw_id.split('_')[0]
                    date = img.get('startdate')
                    copyright_text = img.get('copyright', '')

                    if clean_id not in db:
                        db[clean_id] = {
                            "sort_key": f"{date}_{clean_id}",
                            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                            "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                            "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                            "img_id": clean_id,
                            "title": img.get('title', clean_id),
                            "description": copyright_text,  # Авто-добавление описания
                            "copyright": copyright_text,
                            "markets": [mkt]
                        }
                    else:
                        # Обновляем, если описание было пустым
                        if not db[clean_id].get("description"):
                            db[clean_id]["description"] = copyright_text

                        if mkt not in db[clean_id]["markets"]:
                            db[clean_id]["markets"].append(mkt)

        except Exception as e:
            print(f"Ошибка {mkt}: {e}")

    # Сортировка: новые сверху
    sorted_db = dict(
        sorted(
            db.items(),
            key=lambda i: i[1]["sort_key"],
            reverse=True
        )
    )

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(
            sorted_db,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(f"Архив обновлен. Всего уникальных записей: {len(sorted_db)}")


if __name__ == "__main__":
    fetch_wallpapers()
