import time
import sys
import pickle
from bs4 import BeautifulSoup
from loguru import logger
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from telegram_message import send_telegram_message
from config import *


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

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
    # if no new articles found
    else:
        logger.info("No new articles found")

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
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info("Opening page with Selenium...")
        driver.get(DELISTING_HTML_URL)

        time.sleep(5)  # Allow JavaScript to execute

        html = driver.page_source
        driver.quit()
        logger.info("Page loaded successfully with Selenium.")
        return html

    except Exception as e:
        error = f"Selenium error: {e}"
        logger.error(error)
        sys.exit(error)

def get_articles(html):
    # Parse HTML
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        error = f"HTML parsing error: {e}"
        logger.error(error)
        sys.exit(error)

    # Find script tag with data
    script_tag = soup.find("script", {"id": "__APP_DATA", "type": "application/json"})
    if not script_tag:
        error = "Script tag not found"
        logger.error(error)
        sys.exit(error)

    # Parse JSON data
    try:
        data = json.loads(script_tag.string)
        logger.info("JSON data parsed successfully.")
    except json.JSONDecodeError as e:
        error = f"JSON parsing error: {e}"
        logger.error(error)
        sys.exit(error)

    # Get articles from new structure
    articles_data = data.get("appState", {}).get("loader", {}).get("dataByRouteId", {}).get("d34e", {}).get("catalogDetail", {}).get("articles", [])
    if not articles_data:
        error = "Error getting articles: articles not found"
        logger.error(error)
        sys.exit(error)

    # Extract articles
    articles = []
    for article in articles_data:
        code = article.get("code")
        title = article.get("title")
        if code and title:
            link = f"{BASE_LINK_URL}/en/support/announcement/{code}"
            articles.append((code, link, title))
    if not articles:
        error = "Error getting articles: no valid articles found"
        logger.error(error)
        sys.exit(error)

    logger.info(f"Successfully retrieved {len(articles)} articles.")
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
