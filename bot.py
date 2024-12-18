import os, re
import traceback, time
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.error import  Unauthorized

# Local imports
from botusers import load, save
from logger import getlogger_bot as getlogging
from requestAlive import getLastTimeout
from utils.date import datePeriodName, weekDayStr
from config import config

logging = getlogging()
dataFileName = config['SELENIUM_DATA_JSON_FILENAME']
requestInterval = int(config['REQUEST_SECONDS_INTERVAL'])*60
userIdFileName = config['USERID_FILENAME']
botOwnerId = config['BOTOWNER_ID']
url=config['BUTTON_URL']
markDownSizoName=re.sub(r'([-!.])',r'\\\g<1>' ,config['SIZO_NAME'])
logging.debug(f'url {url}')

openWebUrlkeyboard = InlineKeyboardMarkup.from_button(
    InlineKeyboardButton(text="Записаться!", url=url)
)

minDue = 5

logging.debug(f'config {json.dumps(config, indent=4)}')
messageInterval = 24*60*60
def start(update: Update, context: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        rf'''Привет, {user.mention_markdown_v2()}\!
        Я буду сообщать вам когда появятся места в электронной очереди {markDownSizoName}\!
        Используй команды
        /watch для запуска отслеживания доступных дней
        /unwatch для остановки отслеживания
        /help для подсказки'''
    )
    watch(update, context=context)
userIdValues = load(userIdFileName)
commonContext = None

def sendTimeoutInfo(context: CallbackContext):
    chat_id=botOwnerId
    interval = round(time.time()-getLastTimeout(dataFileName))
    intervalMessageMinimal = requestInterval*1.5
    userIdValues = load(userIdFileName)
    if(interval>intervalMessageMinimal):
        if(time.time()-userIdValues['lastNotifyDateService']>=requestInterval):
            userIdValues['lastNotifyDateService'] = time.time()
            userIdValues['issuefixed'] = 'false'
            context.bot.send_message(chat_id, text=f'Превышен интервал запроса к сайту \
                                     на {interval-requestInterval} секунд')
            save(userIdFileName, userIdValues)
    elif(userIdValues['issuefixed'] == 'false'):
        context.bot.send_message(chat_id, text=f'Соединение с сайтом восстановлено')
        userIdValues['issuefixed'] = 'true'
        save(userIdFileName, userIdValues)

def deleteChatIdStore(chat_id):
    userIdValues = load(userIdFileName)
    if (str(chat_id) in userIdValues['chatIds']):
        del userIdValues["chatIds"][str(chat_id)]
        save(userIdFileName, userIdValues)

def getSnapShotData(data):
    return (','.join(
        (f'{dt["day"]}|{dt["places"]})') for dt in data
    ))

def alarm(context: CallbackContext) -> None:
    global openWebUrlkeyboard
    """Send the alarm message."""
    data = []
    if(os.path.isfile(dataFileName)):
        with open(dataFileName, 'r') as input_file:
            fileData = json.load(input_file)
            if url in fileData:
                data = fileData[url]
    daysQty = len(data)
    userIdValues = load(userIdFileName)

    chatQty = len(userIdValues["chatIds"])
    chatQtyMessage = f'Количество чатов в которых следят за очередью: {chatQty}'
    newUserIdValues = {
        **userIdValues,
        "chatIds": {}
    }

    for chat_id in userIdValues["chatIds"]:
        chatStore = userIdValues["chatIds"][chat_id]
        previousRun = chatStore['lastNotifyDate']
        if (
            chatStore['lastDates'] != getSnapShotData(data)
        ):
            logging.info(f"lastDates {chatStore['lastDates']} != data {getSnapShotData(data)}")
            chatStore['lastNotifyDate'] = time.time()
            chatStore['lastDates'] = getSnapShotData(data)
            logging.debug(f'daysQty {daysQty}')

            try:
                if(daysQty==0):
                    context.bot.send_message(chat_id, text='Отсутствуют дни для записи\n'+\
                                            chatQtyMessage)
                else:
                    daysStr = (', '.join(
                        (str(dt['day'])+
                        f'({weekDayStr(dt["day"])}, мест: {dt["places"]})') for dt in data
                    ))
                    strDatePeriodName = ''.join(datePeriodName({"d": daysQty}))
                    textMsg = f'Есть запись на {strDatePeriodName}:\n{daysStr}\n{chatQtyMessage}'
                    context.bot.send_message(
                        chat_id,
                        text=textMsg,
                        reply_markup=openWebUrlkeyboard
                    )
                newUserIdValues["chatIds"][chat_id] = chatStore
            except Unauthorized as e:
                error_message = traceback.format_exc()
                logging.error(error_message)
                logging.info(f"Удаляем пользователя {chat_id}\n")
                chatQty = chatQty - 1
        else:
            newUserIdValues["chatIds"][chat_id] = chatStore
    save(userIdFileName, newUserIdValues)

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
    global userIdValues
    if not (str(chat_id) in userIdValues['chatIds']):
        userIdValues['chatIds'][chat_id] = {}
        userIdValues['chatIds'][chat_id]['lastDates'] = getSnapShotData([])
        userIdValues['chatIds'][chat_id]['lastNotifyDate'] = 0
        save(userIdFileName, userIdValues)

def watch(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    createChatIdStore(chat_id)

    chatQty = len(userIdValues["chatIds"])
    chatQtyMessage = f'Количество чатов в которых следят за очередью: {chatQty}'
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
            commonContext.job_queue.run_repeating(
                sendTimeoutInfo,
                requestInterval,
                context='service',
                name='service',
                first=1
            )

        text = 'Наблюдение запущено!'
        if job_removed:
            text += ' Предыдущее остановлено.'
        update.message.reply_text(text+'\n'+chatQtyMessage)

    except (IndexError, ValueError):
        error_message = traceback.format_exc()
        update.message.reply_text(
            f'Usage: /watch [<интервал проверки в секундах>]\n{error_message}'
        )
        logging.error(error_message)


def unwatch(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = str(update.message.chat_id)
    userIdValues = load(userIdFileName)
    job_removed = userIdValues['chatIds'].pop(chat_id, None)
    text = 'Наблюдение остановлено!' if job_removed else 'Наблюдение не было запущено.'
    update.message.reply_text(text)
    save(userIdFileName, userIdValues)

def sendallJobD(sendall_message, sendall_start):
    sendAllPrevIdx = -1
    sendAllPrevIdx = 0
    userIdValues = load(userIdFileName)
    userIds = list(userIdValues["chatIds"].keys())
    logging.debug(f'botOwnerId {botOwnerId}')
    def stopSendallJob(context: CallbackContext, userIds) -> None:
        jobName = 'sendall'
        job_removed = remove_job_if_exists(jobName, context)

        text = f'Рассылка остановлена! Разослано {len(userIds)} сообщений! \
            За {time.time()-sendall_start} секунд.'
        if job_removed:
            context.bot.send_message(botOwnerId, text=text)
        else:
            context.bot.send_message(botOwnerId, text='Рассылка не остановлена')
    def sendallJob(context: CallbackContext) -> None:
        if len(userIds) > sendAllPrevIdx+1:
            try:
                sendAllPrevIdx += 1
                chat_id = userIds[sendAllPrevIdx]
                logging.debug(f'{sendAllPrevIdx} chat_id {chat_id}')
                context.bot.send_message(chat_id, text=sendall_message)
                if chat_id == userIds[-1]:
                    stopSendallJob(context, userIds)
            except Unauthorized:
                error_message = traceback.format_exc()
                logging.error(error_message)
                logging.info(f"Удаляем пользователя {chat_id}")
                deleteChatIdStore(chat_id)

            except (IndexError, ValueError ):
                error_message = traceback.format_exc()
                logging.debug(f'Не удалось отправить сообщение по {chat_id}')
                logging.error(error_message)
    return sendallJob

def sendall(update: Update, context: CallbackContext) -> None:
    """Send the alarm message."""
    sender_id = str(update.message.chat_id)
    if sender_id == botOwnerId:
        global commonContext
        sendallJob = sendallJobD(
            sendall_message = " ".join(context.args),
            sendall_start = time.time()
        )

        try:
            # args[0] should contain the url
            due = 5
            jobName = 'sendall'
            job_removed = remove_job_if_exists(jobName, commonContext)
            commonContext.job_queue.run_repeating(
                sendallJob,
                due,
                context=context,
                name=jobName,
                first=1
            )

            current_jobs = commonContext.job_queue.get_jobs_by_name(jobName)

            text = 'Рассылка запущена!'
            if job_removed:
                text += ' Предыдущая остановлена.'
            update.message.reply_text(text)

        except (IndexError, ValueError):
            error_message = traceback.format_exc()
            update.message.reply_text(f'Usage: /sendall [<сообщение>]\n{error_message}')


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
    dispatcher.add_handler(CommandHandler("sendall", sendall))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
