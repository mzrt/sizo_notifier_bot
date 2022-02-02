import os
from dotenv import dotenv_values
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **os.environ,  # override loaded values with environment variables
}

import traceback, time
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging
logging.basicConfig(filename='bot.log', encoding='utf-8', level=logging.INFO)
minDue = 60
logger = logging.getLogger(__name__)


logging.info(f'config {json.dumps(config)}')
messageInterval = 24*60*60
def start(update: Update, context: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    update.message.reply_text('''Привет!
    Я буду сообщать вам когда появятся места в электронной очереди Новосибирского Сизо-1!
    Используй команды
    /watch для запуска отслеживания доступных дней
    /unwatch для остановки отслеживания
    /help для подсказки''')
userIdValues = {}
def alarmGen(chat_id):
    global userIdValues
    userIdValues[chat_id] = {}
    userIdValues[chat_id]['lastDates'] = json.dumps([])
    userIdValues[chat_id]['lastNotifyDate'] = 0
    
    logging.info(f'userIdValues len {len(userIdValues)}')
    def alarm(context: CallbackContext) -> None:
        """Send the alarm message."""
        job = context.job
        
        with open('data.json', 'r') as input_file:
            data = json.load(input_file)
        newDates = data['dates']
        daysQty = len(newDates)
        previousRun = userIdValues[chat_id]['lastNotifyDate']
        logging.info(f'previous run at {previousRun}, {time.time() - previousRun} seconds ago')
        if (\
            (time.time() - previousRun) > messageInterval\
                or userIdValues[chat_id]['lastDates'] != json.dumps(newDates)\
        ):
            userIdValues[chat_id]['lastNotifyDate'] = time.time()
            userIdValues[chat_id]['lastDates'] = json.dumps(newDates)
            logging.info(f'daysQty {daysQty}')
            if(daysQty==0):
                context.bot.send_message(job.context, text=f'Всего следят за очередью: {len(userIdValues)}\nОсутствуют дни для записи')
            else:
                daysStr = (', '.join(str(dt) for dt in newDates))
                textMsg = (
                    f'Всего следят за очередью: {len(userIdValues)}\nЕсть запись на {daysQty} дней:\n{daysStr}'
                )
                keyboard = InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Записаться!", url=config['URL'])
                )
                # Send message with text and appended InlineKeyboard
                # textMsg = f'Есть запись на {daysQty} дней:\n{daysStr}\nПерейти на '+'[сайт]('+data['url']+')'
                context.bot.send_message(job.context, text=textMsg, reply_markup=keyboard )
    return alarm


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def watch(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Наблюдение запущено!")
    try:
        # args[0] should contain the url
        due = minDue
        if len(context.args) > 0:
            due = context.args[1]
        if due < minDue:
            due = minDue

        job_removed = remove_job_if_exists(str(chat_id), context)
        al = alarmGen(str(chat_id))
        context.job_queue.run_repeating(al, due, context=chat_id, name=str(chat_id), first=1)

        text = 'Наблюдение запущено!'
        if job_removed:
            text += ' Предыдущее остановлено.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        error_message = traceback.format_exc()
        update.message.reply_text(f'Usage: /watch [<интервал проверки в секундах>]\n{error_message}')


def unwatch(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Наблюдение остановлено!' if job_removed else 'Наблюдение не было запущено.'
    update.message.reply_text(text)


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    # updater = Updater(token='5228292477:AAHjKQjXP6BEK8TWH2BA0MxHJ63r8k5941E', use_context=True)
    updater = Updater(token=config['BOT_TOKEN'], use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("watch", watch))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("unwatch", unwatch))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()