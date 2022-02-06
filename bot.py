import os
from dotenv import dotenv_values
from botusers import load, save
from requestAlive import getLastTimeout
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **(dotenv_values(".env.development.local") if os.environ['app']=="dev" else {}),
    **os.environ,  # override loaded values with environment variables
}

from utils import datePeriodName
import traceback, time
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging
logging.basicConfig(filename=config['LOG_FILENAME_BOT'], encoding='utf-8', level=logging.INFO)
minDue = 30
logger = logging.getLogger(__name__)

logging.info(f'config {json.dumps(config, indent=4)}')
messageInterval = 24*60*60
def start(update: Update, context: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    update.message.reply_text('''Привет!
    Я буду сообщать вам когда появятся места в электронной очереди Новосибирского Сизо-1!
    Используй команды
    /watch для запуска отслеживания доступных дней
    /unwatch для остановки отслеживания
    /help для подсказки''')
    watch(update, context=context)
userIdValues = load(config['USERID_FILENAME'])
commonContext = None

def sendTimeoutInfo(context: CallbackContext):
    title = 'sendTimeoutInfo'
    chat_id=config['BOTOWNER_ID']
    interval = round(time.time()-getLastTimeout(config['DATA_JSON_FILENAME']))
    requestInterval = int(config['REQUEST_MINUTES_INTERVAL'])*60
    intervalMessageMinimal = requestInterval*1.5
    logging.info(f'{title} 1')
    if(interval>intervalMessageMinimal):
        logging.info(f'{title} 2')
        if(time.time()-userIdValues['lastNotifyDateService']>=int(config['SERVICE_MESSAGE_MINUTES_INTERVAL'])*60):
            logging.info(f'{title} 3')
            userIdValues['lastNotifyDateService'] = time.time()
            userIdValues['issuefixed'] = 'false'
            context.bot.send_message(chat_id, text=f'Превышен интервал запроса к сайту на {interval-requestInterval} секунд')
            save(config['USERID_FILENAME'], userIdValues)
    elif(userIdValues['issuefixed'] == 'false'):
        logging.info(f'{title} 4')
        context.bot.send_message(chat_id, text=f'Соединение с сайтом восстановлено')
        userIdValues['issuefixed'] = 'true'
        save(config['USERID_FILENAME'], userIdValues)


openWebUrlkeyboard = InlineKeyboardMarkup.from_button(
    InlineKeyboardButton(text="Записаться!", url=config['BUTTON_URL'])
)
def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    data = {'dates':[]}
    if(os.path.isfile(config['DATA_JSON_FILENAME'])):
        with open(config['DATA_JSON_FILENAME'], 'r') as input_file:
            data = json.load(input_file)
    newDates = data['dates']
    daysQty = len(newDates)
    
    chatQty = len(userIdValues["chatIds"])
    chatQtyMessage = f'Количество чатов в которых следят за очередью: {chatQty}'
    for chat_id in userIdValues["chatIds"]:
        chatStore = userIdValues["chatIds"][chat_id]
        previousRun = chatStore['lastNotifyDate']
        logging.info(f'previous run at {previousRun}, {time.time() - previousRun} seconds ago')
        if (\
            (time.time() - previousRun) > messageInterval\
                or chatStore['lastDates'] != json.dumps(newDates)\
        ):
            chatStore['lastNotifyDate'] = time.time()
            chatStore['lastDates'] = json.dumps(newDates)
            save(config['USERID_FILENAME'], userIdValues)
            logging.info(f'daysQty {daysQty}')
            if(daysQty==0):
                context.bot.send_message(chat_id, text='Осутствуют дни для записи\n'+chatQtyMessage)
            else:
                daysStr = (', '.join(str(dt) for dt in newDates))
                strDatePeriodName = ''.join(datePeriodName({"d": daysQty}))
                textMsg = f'Есть запись на {strDatePeriodName}:\n{daysStr}\n{chatQtyMessage}'
                context.bot.send_message(chat_id, text=textMsg, reply_markup=openWebUrlkeyboard )


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    global commonContext
    if(commonContext is None):
        commonContext = context
    current_jobs = commonContext.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def createChatIdStore(chat_id):
    title = 'createChatIdStore'
    logging.info(f'{title} chat_id {chat_id} 1')
    global userIdValues
    if not (str(chat_id) in userIdValues['chatIds']):
        logging.info(f'{title} 2')
        userIdValues['chatIds'][chat_id] = {}
        userIdValues['chatIds'][chat_id]['lastDates'] = json.dumps([])
        userIdValues['chatIds'][chat_id]['lastNotifyDate'] = 0
        save(config['USERID_FILENAME'], userIdValues)

def watch(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    createChatIdStore(chat_id)
    global commonContext
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Наблюдение запущено!")
    try:
        # args[0] should contain the url
        due = minDue
        if len(context.args) > 0:
            due = context.args[1]
        if due < minDue:
            due = minDue
        jobName = 'notify'
        job_removed = remove_job_if_exists(jobName, context)
        commonContext.job_queue.run_repeating(alarm, due, context=jobName, name=jobName, first=1)
        
        current_jobs = commonContext.job_queue.get_jobs_by_name('service')
        if not current_jobs:
            commonContext.job_queue.run_repeating(sendTimeoutInfo, int(config['REQUEST_MINUTES_INTERVAL'])*60, context='service', name='service', first=1)

        text = 'Наблюдение запущено!'
        if job_removed:
            text += ' Предыдущее остановлено.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        error_message = traceback.format_exc()
        update.message.reply_text(f'Usage: /watch [<интервал проверки в секундах>]\n{error_message}')


def unwatch(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = str(update.message.chat_id)
    global userIdValues
    job_removed = userIdValues['chatIds'].pop(chat_id, None)
    text = 'Наблюдение остановлено!' if job_removed else 'Наблюдение не было запущено.'
    update.message.reply_text(text)


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
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