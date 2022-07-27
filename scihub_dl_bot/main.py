from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters
from telegram import Update
from bs4 import BeautifulSoup
import re
import requests
import dotenv
import logging
import os

def verify_doi(doi_link: str) -> bool:
    if re.match(r"http[s]?:\/\/doi.org\/10.\d{4,6}\/[A-Za-z0-9.-\/]+", doi_link):
        return True
    else:
        return False

def doi(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id  # type: ignore
    doi_link = update.message.text

    if verify_doi(doi_link):
        logging.info(f"DOI Code from id: '{chat_id}'")
        context.bot.send_message(
            chat_id=chat_id, text=f"Searching for: {doi_link}")

        req = requests.get(f"https://sci-hub.se/{doi_link}")
        if req.status_code == 404:
            context.bot.send_message(
                chat_id=chat_id, text=f"Article {doi_link[15:]} does not exist.")
        if req.status_code == 200:
            try:
                soup = BeautifulSoup(req.content, 'html.parser')
                pdf_path = soup.find_all(id='pdf')[0].get('src')
                if 'sci-hub.se' in pdf_path or pdf_path.startswith("//"):
                    pdf_link = f"http:{pdf_path}"
                else:
                    pdf_link = f"https://sci-hub.se/{pdf_path}"
                context.bot.send_message(
                    chat_id=chat_id, text=f"Downloading {pdf_link}")
                context.bot.send_document(
                    chat_id, f"{pdf_link}")
            except:
                context.bot.send_message(
                    chat_id=chat_id, text="Unfortunately, Sci-Hub doesn't have the requested document.")
        if req.status_code == 300:
            context.bot.send_message(
                chat_id=chat_id, text="Timeout! Please Try again Later.")

    else:
        logging.warning(f"Invalid DOI link from id: '{chat_id}'")
        context.bot.send_message(
            chat_id=chat_id, text=f"Error: Not a valid DOI link.")


def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id  # type: ignore
    logging.info(f"/start from id: '{chat_id}'")
    context.bot.send_message(
        chat_id=chat_id, text="Welcome to SciHub Downloader! Please send DOI link to download.")  # type: ignore


def help_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id # type: ignore
    logging.info(f"/help from id: '{chat_id}'")
    context.bot.send_message(chat_id, "Send DOI Link in following format: \nhttps://doi.org/10.xxxx/abc123")


def main():
    dotenv.load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')

    updater = Updater(token=TOKEN) #type: ignore
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help_command)
    doi_handler = MessageHandler(Filters.text & (~Filters.command), doi)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(doi_handler)

    updater.start_polling()

if __name__ == "__main__":
    main()