import os
from dotenv import load_dotenv, find_dotenv

# Loading .env variables
load_dotenv(find_dotenv())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if TELEGRAM_TOKEN is None:
    raise Exception("Please setup the .env variable TELEGRAM_TOKEN.")

PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

TELEGRAM_SUPPORT_CHAT_ID = os.getenv("TELEGRAM_SUPPORT_CHAT_ID")
if TELEGRAM_SUPPORT_CHAT_ID is None or not str(TELEGRAM_SUPPORT_CHAT_ID).lstrip("-").isdigit():
    raise Exception("You need to specify 'TELEGRAM_SUPPORT_CHAT_ID' env variable: The bot will forward all messages to this chat_id. Add this bot https://t.me/ShowJsonBot to your private chat to find its chat_id.")
TELEGRAM_SUPPORT_CHAT_ID = int(TELEGRAM_SUPPORT_CHAT_ID)


WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "👋")

TRELLO_DORM_IDLIST = {
    'ГЗ': '5d491ea65f2dce023c5237e8',
    'ДСЛ': '5d4916a59457c06e21cdf441',
    'ФДС': '5d4924e8c2ef6b4b45ca2a46',
    'ДСВ': '5d49250b9ba68c1bbe7f94e8',
    'ДСК': '5d49250b9ba68c1bbe7f94e8',
    'ДСШ': '5d49250b9ba68c1bbe7f94e8',
    'ДСЯ': '5d49250b9ba68c1bbe7f94e8'
}
