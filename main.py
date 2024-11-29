import requests
import sys
import pickle
from bs4 import BeautifulSoup
from loguru import logger
import json
import sentry_sdk
from telegram_message import send_telegram_message
from config import *

def main():
    # add logger
    logger.add("main.log", rotation="10 MB", encoding="utf8")

    # sentry
    use_sentry()

    # read unique article codes from file
    codes = read_codes()

    # get html from url
    html = get_html()

    # get articles from html
    articles = get_articles(html)

    # if the codes are empty, it means this is the first run of the script
    if not len(codes):
        logger.info("Initial run of the script, saving codes")
        codes = get_codes_from_articles(articles)
        write_codes(codes)
        sys.exit()

    # check for new articles
    new_articles = [article for article in articles if article[0] not in codes]

    # if there are new articles found
    if len(new_articles):
        logger.info(f"New articles found: {len(new_articles)}")

        # save new codes to the file merging with the old ones
        new_codes = get_codes_from_articles(new_articles)
        codes += new_codes
        write_codes(list(set(codes)))

        # send new articles to telegram
        for article in new_articles:
            send_article_to_telegram(article)

def use_sentry():
    try:
        if USE_SENTRY:
            import sentry_sdk
            sentry_sdk.init(dsn=SENTRY_DNS)
    except NameError:
        pass

def read_codes():
    try:
        with open(CODES_FILENAME, 'rb') as f:
            records = pickle.load(f)
    except FileNotFoundError:
        logger.warning(f"File {CODES_FILENAME} does not exist")
        return []
    except Exception as e:
        error = f"Error loading data from {CODES_FILENAME}: {e}"
        logger.error(error)
        sys.exit(error)
    else:
        logger.info(f"Got {len(records)} codes from {CODES_FILENAME}")
        return records

def write_codes(codes):
    try:
        with open(CODES_FILENAME, 'wb') as f:
            pickle.dump(codes, f)
    except Exception as e:
        error = f"Error writing codes: {e}"
        logger.error(error)
        sys.exit(error)
    else:
        logger.info(f"Codes ({len(codes)}) were written to {CODES_FILENAME}")


def get_html():
    try:
        response = requests.get(DELISTING_HTML_URL)
    except Exception as e:
        error = f"Get URL error: {e}"
        logger.error(error)
        sys.exit(error)
    else:
        if response.status_code == 200:
            html = response.text
        else:
            error = f"Get URL error with response code {response.status_code}"
            logger.error(error)
            sys.exit(error)
        return html

def get_articles(html):
    # parse html
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        error = f"HTML parsing error: {e}"
        logger.error(error)
        sys.exit(error)

    # find script tag with data
    script_tag = soup.find("script", {"id": "__APP_DATA", "type": "application/json"})
    if not script_tag:
        error = "Script tag not found"
        logger.error(error)
        sys.exit(error)

    # parse JSON data
    try:
        data = json.loads(script_tag.string)
    except json.JSONDecodeError as e:
        error = f"JSON parsing error: {e}"
        logger.error(error)
        sys.exit(error)

    # get catalogs
    catalogs = data.get("appState", {}).get("loader", {}).get("dataByRouteId", {}).get("d9b2", {}).get("catalogs", [])
    if not len(catalogs):
        error = "Error getting catalogs: catalogs not found"
        logger.error(error)
        sys.exit(error)

    # get articles
    articles = []
    for catalog in catalogs:
        if catalog.get("catalogName") == "Delisting":
            for article in catalog.get("articles", []):
                code = article.get("code")
                title = article.get("title")
                if code and title:
                    link = f"{BASE_LINK_URL}/en/support/announcement/{code}"
                    articles.append((code, link, title))
    if not len(articles):
        error = "Error getting articles: articles not found"
        logger.error(error)
        sys.exit(error)

    return articles

def get_codes_from_articles(articles):
    return [article[0] for article in articles]

def send_article_to_telegram(article):
    link = article[1]
    title = article[2]
    try:
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, f"{title}\n{link}")
    except Exception as e:
        error = f"Error sending telegram message: {e}"
        logger.error(error)
        sys.exit(error)
    else:
        logger.info(f"New link sent to telegram: {link}")

if __name__ == '__main__':
    main()
