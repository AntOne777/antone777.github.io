import json
import os
import sys
import time
import re
import gzip
from pathlib import Path
from tempfile import NamedTemporaryFile
import urllib.request
import urllib.parse
import urllib.error

MARKETS = [
    "en-US", "en-AU", "en-CA", "zh-CN", "de-DE", "es-ES", "fr-FR",
    "it-IT", "ja-JP", "en-NZ", "en-GB", "nl-NL", "pl-PL", "pt-BR",
    "pt-PT", "ko-KR", "ru-RU",
]

DATA_FILE = Path("data.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
}

REQUEST_TIMEOUT = 30
_MARKET_SUFFIX = re.compile(r"_[A-Z]{2}(?:-[A-Z]{2})?\d+$", re.IGNORECASE)


def fetch_json_with_retry(api_url, params, headers, max_retries=3):
    query_string = urllib.parse.urlencode(params)
    url = f"{api_url}?{query_string}"
    req = urllib.request.Request(url, headers=headers)
    
    retry_status_codes = {429, 500, 502, 503, 504}
    
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                body = response.read()
                
                # Мягкая проверка на gzip
                encoding = (response.info().get("Content-Encoding") or "").lower()
                if "gzip" in encoding:
                    body = gzip.decompress(body)
                    
                return json.loads(body.decode("utf-8"))
                
        except urllib.error.HTTPError as error:
            # Обязательно освобождаем сокет при ошибке ответа сервера
            error.close()
            if error.code in retry_status_codes and attempt < max_retries:
                time.sleep(1 * (2 ** attempt))
                continue
            raise
            
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            if attempt < max_retries:
                time.sleep(1 * (2 ** attempt))
                continue
            raise


def load_database():
    if not DATA_FILE.exists():
        return {}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        print(f"Ошибка: файл {DATA_FILE} содержит некорректный JSON: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except OSError as error:
        print(f"Ошибка чтения файла {DATA_FILE}: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    if not isinstance(data, dict):
        print(f"Ошибка: файл {DATA_FILE} должен содержать JSON-объект.", file=sys.stderr)
        raise SystemExit(1)

    return data


def get_image_id(urlbase, start_date):
    if "?id=OHR." in urlbase:
        raw_id = urlbase.split("?id=OHR.", 1)[1]
    else:
        raw_id = urlbase.rsplit("/", 1)[-1]

    raw_id = raw_id.split("&", 1)[0]
    raw_id = _MARKET_SUFFIX.sub("", raw_id)

    return raw_id or f"bing-{start_date}"


def build_entry(image, clean_id):
    urlbase = image.get("urlbase") or ""
    start_date = image.get("startdate") or ""
    
    copyright_text = (image.get("copyright") or "").strip()
    title = image.get("title") or clean_id

    return {
        "sort_key": f"{start_date}_{clean_id}",
        "date": f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
        "url": f"https://www.bing.com{urlbase}_UHD.jpg",
        "preview": f"https://www.bing.com{urlbase}_1920x1080.jpg",
        "img_id": clean_id,
        "title": title,
        "description": copyright_text,
        "copyright": copyright_text,
        "markets": [],
    }


def update_entry(entry, image, market):
    copyright_text = (image.get("copyright") or "").strip()
    markets = entry.setdefault("markets", [])

    if market not in markets:
        markets.append(market)

    if not entry.get("description") and copyright_text:
        entry["description"] = copyright_text

    if not entry.get("copyright") and copyright_text:
        entry["copyright"] = copyright_text

    if not entry.get("title"):
        entry["title"] = image.get("title") or entry["img_id"]


def fetch_wallpapers():
    database = load_database()

    successful_markets = 0
    received_images = 0

    for market in MARKETS:
        api_url = "https://www.bing.com/HPImageArchive.aspx"
        params = {
            "format": "js",
            "idx": 0,
            "n": 5,
            "mkt": market,
        }

        try:
            payload = fetch_json_with_retry(api_url, params, HEADERS)
            images = payload.get("images", [])

            if not isinstance(images, list):
                raise ValueError("Поле images имеет неправильный формат")

            successful_markets += 1
            received_images += len(images)

            for image in images:
                if not isinstance(image, dict):
                    continue

                urlbase = image.get("urlbase", "")
                start_date = image.get("startdate", "")

                if not urlbase or len(start_date) != 8 or not start_date.isdigit():
                    continue

                clean_id = get_image_id(urlbase, start_date)

                if not clean_id:
                    continue

                if clean_id not in database:
                    database[clean_id] = build_entry(image, clean_id)

                update_entry(database[clean_id], image, market)

            print(f"{market}: получено изображений — {len(images)}")

        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"Ошибка запроса для {market}: {error}", file=sys.stderr)

        except (ValueError, TypeError, KeyError) as error:
            print(f"Ошибка обработки данных для {market}: {error}", file=sys.stderr)

    if successful_markets == 0:
        print("Ошибка: не удалось получить данные ни для одного рынка.", file=sys.stderr)
        raise SystemExit(1)

    sorted_database = dict(
        sorted(
            database.items(),
            key=lambda item: str(item[1].get("sort_key", "")),
            reverse=True,
        )
    )

    write_database(sorted_database)

    print(
        "Архив обновлён. "
        f"Успешных рынков: {successful_markets}/{len(MARKETS)}. "
        f"Получено изображений: {received_images}. "
        f"Всего уникальных записей: {len(sorted_database)}."
    )


def write_database(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_FILE.parent,
            prefix=f"{DATA_FILE.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(data, temporary_file, ensure_ascii=False, indent=4)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)

        os.replace(temporary_path, DATA_FILE)

    except OSError as error:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)

        print(f"Ошибка записи файла {DATA_FILE}: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    fetch_wallpapers()
