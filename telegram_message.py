import requests

def send_telegram_message(bot_token, chat_id, message):

    api_url = "https://api.telegram.org/bot{}/".format(bot_token)
    method = 'sendMessage'
    params = {
            'parse_mode': 'markdown',
            'disable_web_page_preview': 'false',
            'chat_id': chat_id,
            'text': message
            }
    
    response = requests.post(api_url + method, params)

    return response
