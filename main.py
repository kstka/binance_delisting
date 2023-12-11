import requests
import sys
import pickle
import sentry_sdk
from telegram_message import send_telegram_message
from config import *

if __name__ == '__main__':

    # sentry
    try:
        if USE_SENTRY:
            import sentry_sdk
            sentry_sdk.init(dsn=SENTRY_DNS)
    except NameError:
        pass

    # read records file
    records = []
    try:
        with open(RECORDS_FILENAME, 'rb') as f:
            records = pickle.load(f)
    except FileNotFoundError:
        print(f"File {RECORDS_FILENAME} does not exist")
    except Exception as e:
        sys.exit(f"Error loading data from {RECORDS_FILENAME}: {e}")
    else:
        print(f"Got {len(records)} records from {RECORDS_FILENAME}")

    # get data from url
    try:
        response = requests.get(DELISTING_API_URL)
    except Exception as e:
        sys.exit(f"Get URL error: {e}")
    else:
        print(f"API URL response is {response}")

    # load articles
    try:
        articles = response.json()['data']['articles']
    except Exception as e:
        sys.exit(f"Error loading articles: {e}")
    else:
        print(f"Loaded {len(articles)} articles from URL")

    # check for new articles
    if len(records):
        for item in articles:

            # skip known ids
            if item['id'] in records:
                continue

            # new article url
            link = BASE_LINK_URL + item['code']
            
            # send link to telegram channel
            try:
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, f"{item['title']}\n{link}")
            except Exception as e:
                sys.exit(f"Error sending telegram message: {e}")
            else:
                print(f"New link sent to telegram: {link}")

            # save new id to records file
            try:
                with open(RECORDS_FILENAME, 'wb') as f:
                    records.append(item['id'])
                    pickle.dump(records, f)
            except Exception as e:
                sys.exit(f"Error saving records: {e}")
            else:
                print(f"New id {item['id']} saved to {RECORDS_FILENAME}")

    # if records are empty just save all articles ids
    if not len(records) and len(articles):
        records = [article['id'] for article in articles]
        try:
            with open(RECORDS_FILENAME, 'wb') as f:
                pickle.dump(records, f)
        except Exception as e:
            sys.exit(f"Error saving initial records {', '.join(str(i) for i in records)}: {e}")
        else:
            print(f"Initial records {', '.join(str(i) for i in records)} saved to {RECORDS_FILENAME}")
