import json
import os

import requests

MARKETS = [
    "en-US", "en-AU", "en-CA", "zh-CN", "de-DE", "es-ES",
    "fr-FR", "it-IT", "ja-JP", "en-NZ", "en-GB", "nl-NL",
    "pl-PL", "pt-BR", "pt-PT", "ko-KR", "ru-RU",
]

DATA_FILE = "data.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/127.0.0.0 Safari/537.36"
    )
}


def load_database():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def fetch_wallpapers():
    db = load_database()

    for market in MARKETS:
        try:
            api_url = (
                "https://www.bing.com/HPImageArchive.aspx"
                f"?format=js&idx=0&n=5&mkt={market}"
            )

            response = requests.get(
                api_url,
                headers=HEADERS,
                timeout=15,
            )
            response.raise_for_status()

            for image in response.json().get("images", []):
                urlbase = image.get("urlbase", "")
                date = image.get("startdate", "")

                if not urlbase or len(date) != 8:
                    continue

                raw_id = (
                    urlbase.split("?id=OHR.", 1)[-1]
                    if "?id=OHR." in urlbase
                    else urlbase.rsplit("/", 1)[-1]
                )
                clean_id = raw_id.split("_", 1)[0]

                if not clean_id:
                    continue

                copyright_text = image.get("copyright", "")
                entry = db.setdefault(
                    clean_id,
                    {
                        "sort_key": f"{date}_{clean_id}",
                        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                        "url": f"https://www.bing.com{urlbase}_UHD.jpg",
                        "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
                        "img_id": clean_id,
                        "title": image.get("title") or clean_id,
                        "description": copyright_text,
                        "copyright": copyright_text,
                        "markets": [],
                    },
                )

                entry.setdefault("markets", [])

                if not entry.get("description"):
                    entry["description"] = copyright_text

                if not entry.get("copyright"):
                    entry["copyright"] = copyright_text

                if market not in entry["markets"]:
                    entry["markets"].append(market)

        except requests.RequestException as error:
            print(f"Ошибка запроса для {market}: {error}")
        except (ValueError, KeyError) as error:
            print(f"Ошибка обработки данных для {market}: {error}")

    sorted_db = dict(
        sorted(
            db.items(),
            key=lambda item: item[1].get("sort_key", ""),
            reverse=True,
        )
    )

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(sorted_db, file, ensure_ascii=False, indent=4)

    print(f"Архив обновлён. Всего уникальных записей: {len(sorted_db)}")


if __name__ == "__main__":
    fetch_wallpapers()
