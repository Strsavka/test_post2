import logging
import json
import sqlite3
import datetime as dt
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler

# TOKEN for Telegram-bot is necessary
BOT_TOKEN = '7709651633:AAFaD57pRleeEFFqQcx4gHeNQUlqEqvJ7dk'

# logging in
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# mark_ups making
keyboard_for_menu = [[KeyboardButton('/get'), KeyboardButton('/send')],
                     [KeyboardButton('Инструктаж'), KeyboardButton('/change')],
                     [KeyboardButton('/start')]]

data = []

markup_menu = ReplyKeyboardMarkup(keyboard_for_menu)

stop_button = [[KeyboardButton('/stop')]]
markup_stop = ReplyKeyboardMarkup(stop_button)

next_button = [[KeyboardButton('Продолжить')], [KeyboardButton('/stop')]]
markup_next = ReplyKeyboardMarkup(next_button)

# database connection
connection = sqlite3.connect("homework_database.sqlite")
cursor = connection.cursor()


class ActiveHomework:
    def __init__(self):
        self.homework = ''
        self.date = ()
        self.subject = ''
        self.class_of_user = 0
        self.letter_of_class = ''


class ChangingInformation:
    def __init__(self):
        self.class_of_user = ''
        self.letter_of_class = ''


class NoHomeworkError(Exception):
    pass


async def text_answer(updater, context):
    if updater.message.text == 'Инструктаж':
        await updater.message.reply_text('Отправьте команду /get для того чтобы получить домашнее задание')
        await updater.message.reply_text('Отправьте команду /send для того чтобы отправить домашнее задание')
        await updater.message.reply_text('Отправьте команду /change для того чтобы сменить свой класс')
        await updater.message.reply_text('Команда /stop прервёт любую операцию')
        await updater.message.reply_text('Команда /start перезапустит бота')
    else:
        await updater.message.reply_text('Запрос не принят')


async def start(updater, context):
    # Adding new users to client's database
    try:
        chat_id = updater.message.chat.id
        first_name = updater.message.chat.first_name
        username = updater.message.chat.username
        if updater.message.chat.id not in list(map(lambda x: x[0], cursor.execute('''SELECT telegram_id FROM users''').fetchall())):
            cursor.execute('''INSERT INTO users(name, telegram_id, username) VALUES(?, ?, ?)''',
                           (first_name, chat_id, username))
            connection.commit()
            await updater.message.reply_text(f'Привет {first_name}! Я телеграм-бот, работающий на ГБОУ'
                                             f' УР Лицей №41, предназначен для помощи лицеистам получать домашнее задание')
            classes = list(map(lambda x: [KeyboardButton(x)], data.keys())) + [[KeyboardButton('/stop')]]
            numbers_of_class_markup = ReplyKeyboardMarkup(classes)
            await updater.message.reply_text(f'Чтобы было проще сразу выбери класс в котором ты учишься',
                                             reply_markup=numbers_of_class_markup)
            return 2
        else:
            await updater.message.reply_text(f'Привет {first_name}, похоже ты у нас уже был, если ты забыл как '
                                             f'работать со мной то просто вызови инструкцию', reply_markup=markup_menu)
    except Exception as e:
        await error(updater, context, e)


async def change_class(updater, context):
    try:
        classes = list(map(lambda x: [KeyboardButton(x)], data.keys())) + [[KeyboardButton('/stop')]]
        numbers_of_class_markup = ReplyKeyboardMarkup(classes)
        await updater.message.reply_text('Чтобы сменить класс нажмите на нужную цифру класса',
                                         reply_markup=numbers_of_class_markup)
        return 2
    except Exception as e:
        await error(updater, context, e)


async def change_letter_of_class(updater, context):
    try:
        if updater.message.text in data.keys():
            info.class_of_user = updater.message.text
            classes = list(map(lambda x: [KeyboardButton(x)], data[info.class_of_user].keys())) + [[KeyboardButton('/stop')]]
            letters_of_class_markup = ReplyKeyboardMarkup(classes)
            await updater.message.reply_text('Нажмите на нужную букву класса',
                                             reply_markup=letters_of_class_markup)
            return 1
        else:
            await updater.message.reply_text('Нет такого класса, попробуйте заново')
            return 2
    except Exception as e:
        await error(updater, context, e)


async def class_asking(updater, context):
    # Getting class of user and rewrite if needed
    try:
        if updater.message.text in data[info.class_of_user].keys():
            info.letter_of_class = updater.message.text
            cursor.execute('''UPDATE users SET (class, letter_of_class) = (?, ?) WHERE telegram_id = ?''',
                           (int(info.class_of_user), info.letter_of_class, updater.message.chat.id))
            connection.commit()
            await updater.message.reply_text(f'Класс изменён на {info.class_of_user} {info.letter_of_class}',
                                             reply_markup=markup_menu)
            return ConversationHandler.END
        else:
            await updater.message.reply_text('Нет такой буквы класса')
            return 1
    except Exception as e:
        await error(updater, context, e)


async def stop(updater, context):
    # Function to stop any conversations
    await updater.message.reply_text('OK', reply_markup=markup_menu)
    return ConversationHandler.END


async def error(updater, context, mistake):
    # Function to show errors
    await updater.message.reply_text('Извините, произошла ошибка', reply_markup=markup_menu)
    print(mistake)


async def asking_for_ban(updater, context):
    try:
        if str(updater.message.chat.id) == '1986406020':
            users = cursor.execute('''SELECT telegram_id FROM users''').fetchall()
            users = list(map(lambda x: [KeyboardButton(str(x[0]))], users)) + [[KeyboardButton('/stop')]]
            user_markup = ReplyKeyboardMarkup(users)
            await updater.message.reply_text('Выберите пользователя для бана', reply_markup=user_markup)
            return 1
        else:
            await updater.message.reply_text('Запрещено в использовании')
            return ConversationHandler.END
    except Exception as e:
        await error(updater, context, e)


async def ban(updater, context):
    try:
        if updater.message.text in list(map(lambda x: str(x[0]),
                                            cursor.execute('''SELECT telegram_id FROM users''').fetchall())):
            cursor.execute('''UPDATE users SET banned_or_no = 'banned' WHERE telegram_id = ?''',
                           (updater.message.text,))
            connection.commit()
            await updater.message.reply_text('Операция успешно выполнена', reply_markup=markup_menu)
            return ConversationHandler.END
    except Exception as e:
        await error(updater, context, e)


async def print_users(updater, context):
    try:
        if str(updater.message.chat.id) == '1986406020':
            all_users = cursor.execute('''SELECT * FROM users''').fetchall()
            for user in all_users:
                await updater.message.reply_text(user)
    except Exception as e:
        await error(updater, context, e)


async def asking_for_unban(updater, context):
    try:
        if str(updater.message.chat.id) == '1986406020':
            users = cursor.execute('''SELECT telegram_id FROM users''').fetchall()
            users = list(map(lambda x: [KeyboardButton(str(x[0]))], users)) + [[KeyboardButton('/stop')]]
            user_markup = ReplyKeyboardMarkup(users)
            await updater.message.reply_text('Выберите пользователя для разбана', reply_markup=user_markup)
            return 1
        else:
            await updater.message.reply_text('Запрещено в использовании')
            return ConversationHandler.END
    except Exception as e:
        await error(updater, context, e)


async def unban(updater, context):
    try:
        if updater.message.text in list(map(lambda x: str(x[0]),
                                            cursor.execute('''SELECT telegram_id FROM users''').fetchall())):
            cursor.execute('''UPDATE users SET banned_or_no = 'clear' WHERE telegram_id = ?''',
                           (updater.message.text,))
            connection.commit()
            await updater.message.reply_text('Операция успешно выполнена', reply_markup=markup_menu)
            return ConversationHandler.END
    except Exception as e:
        await error(updater, context, e)


async def send(updater, context):
    try:
        # Command function to start uploading_homework_handler
        if cursor.execute('''SELECT banned_or_no FROM users WHERE telegram_id = ?''', (str(updater.message.chat.id),)).fetchone()[0] == 'banned':
            await updater.message.reply_text('Автор запретил вам пользоваться функцией отправки')
            return ConversationHandler.END
        await updater.message.reply_text('Напишите на какое число вы бы хотели отправить дз', reply_markup=markup_stop)
        await updater.message.reply_text('Пишите через дату в формате ДД.ММ.ГГГГ')
        homework.date = None
        return 2
    except Exception as e:
        await error(updater, context, e)


async def getting_date(updater, context):  # Function to get date and to ask subject
    try:
        global data
        if updater.message.text == 'Продолжить':
            new_date = dt.date(homework.date[2], homework.date[1], homework.date[0])
        else:
            string_date = updater.message.text.split('.')
            if len(string_date) != 3:
                raise Exception
            new_date = dt.date(int(string_date[2]), int(string_date[1]), int(string_date[0]))
            homework.date = (int(string_date[0]), int(string_date[1]), int(string_date[2]))

            user_class = cursor.execute('''SELECT class, letter_of_class FROM users WHERE telegram_id = ?''',
                                        (updater.message.chat.id,)).fetchall()
            homework.class_of_user, homework.letter_of_class = user_class[0][0], user_class[0][1]

            if homework.class_of_user is None or homework.letter_of_class is None:
                await updater.message.reply_text('У вас не указан класс, поэтому напиши цифру класса и букву класса '
                                                 'через пробел')
                return 1
        if new_date.weekday() == 6:
            await updater.message.reply_text('Выходной, введите другую дату')
            return 2
        else:
            lessons = (data[str(homework.class_of_user)][homework.letter_of_class][str(new_date.weekday() + 1)] +
                       [['/stop']])
            await updater.message.reply_text('Отлично, теперь выберите урок на который запланировано дз',
                                             reply_markup=ReplyKeyboardMarkup(lessons))
            return 3
    except Exception as e:
        print(e, )
        await updater.message.reply_text('Некорректная дата')
        await updater.message.reply_text('Попробуйте ещё раз')
        return 2


async def class_asking_in_dialog(updater, context):
    # Getting class of user and rewrite if needed
    try:
        user_class = updater.message.text.split()
        if user_class[0] in data.keys():
            if user_class[1] in data[user_class[0]]:
                await updater.message.reply_text('Нажмите продолжить', reply_markup=markup_next)
                homework.class_of_user, homework.letter_of_class = user_class[0], user_class[1]
                return 2
            else:
                await updater.message.reply_text('Некорректный ввод, попробуйте ещё раз, цифру, букву, через пробел, '
                                                 'в русской раскладке')
                return 1
        else:
            await updater.message.reply_text('Некорректный ввод, попробуйте ещё раз, цифру, букву, через пробел, '
                                             'в русской раскладке')
            return 1
    except Exception as e:
        await error(updater, context, e)


async def asking_subject(updater, context):  # Function to get subject and to ask for homework
    try:
        new_date = dt.date(homework.date[2], homework.date[1], homework.date[0])
        list_of_lessons = list(map(lambda x: x[0].text, data[str(homework.class_of_user)][homework.letter_of_class][str(new_date.weekday() + 1)]))
        if updater.message.text.strip() not in list_of_lessons:
            await updater.message.reply_text('Нет такого урока на этот день')
            return 3
        await updater.message.reply_text('Отправьте дз', reply_markup=markup_stop)
        homework.subject = updater.message.text
        return 4
    except Exception as e:
        await error(updater, context, e)


async def asking_homework(updater, context):  # Function to get homework and to upload it
    try:
        homework.homework = updater.message.text
        cursor.execute('''INSERT INTO homework(homework, date, month, year, subject, class, letter_of_class, sender) 
                             VALUES(?, ?, ?, ?, ?, ?, ?, ?)''', (homework.homework, homework.date[0], homework.date[1],
                                                              homework.date[2], homework.subject, homework.class_of_user,
                                                              homework.letter_of_class, updater.message.chat.id))
        connection.commit()
        await updater.message.reply_text('Домашнее задание отправлено', reply_markup=markup_menu)
        return ConversationHandler.END
    except Exception as e:
        print(e)
        await updater.message.reply_text('Попробуйте ещё раз')
        return 4


async def get(updater, context):  # Command function to start downloading_homework_handler
    await updater.message.reply_text('Напишите за какое число вы бы хотели получить дз', reply_markup=markup_stop)
    await updater.message.reply_text('Пишите через дату в формате ДД.ММ.ГГГГ')
    return 2


async def getting_date_to_get(updater, context):  # Function to get date and to ask subject
    try:
        global data
        if updater.message.text == 'Продолжить':
            new_date = dt.date(homework.date[2], homework.date[1], homework.date[0])
        else:
            string_date = updater.message.text.split('.')
            if len(string_date) != 3:
                raise Exception
            new_date = dt.date(int(string_date[2]), int(string_date[1]), int(string_date[0]))
            homework.date = (int(string_date[0]), int(string_date[1]), int(string_date[2]))

            user_class = cursor.execute('''SELECT class, letter_of_class FROM users WHERE telegram_id = ?''',
                                        (updater.message.chat.id,)).fetchall()
            homework.class_of_user, homework.letter_of_class = user_class[0][0], user_class[0][1]

            if homework.class_of_user is None or homework.letter_of_class is None:
                await updater.message.reply_text('У вас не указан класс, поэтому напиши цифру класса и букву класса '
                                                 'через пробел')
                return 1
        if new_date.weekday() == 6:
            await updater.message.reply_text('Выходной, введите другую дату')
            return 2
        else:
            lessons = (data[str(homework.class_of_user)][homework.letter_of_class][str(new_date.weekday() + 1)] +
                       [['/stop']])
            await updater.message.reply_text('Отлично, теперь выберите урок на который запланировано дз',
                                             reply_markup=ReplyKeyboardMarkup(lessons))
            return 3
    except Exception as e:
        print(e)
        await updater.message.reply_text('Некорректная дата')
        await updater.message.reply_text('Попробуйте ещё раз')
        return 2


async def asking_subject_to_get(updater, context):  # Function to get subject and to download homework and to send it
    try:
        new_date = dt.date(homework.date[2], homework.date[1], homework.date[0])
        list_of_lessons = list(map(lambda x: x[0].text, data[str(homework.class_of_user)][homework.letter_of_class][
            str(new_date.weekday() + 1)]))
        if updater.message.text.strip() not in list_of_lessons:
            await updater.message.reply_text('Нет такого урока на этот день')
            return 3
        homework.subject = updater.message.text
        downloaded_homework = cursor.execute('''SELECT homework FROM homework WHERE date = ? and month = ? and year = ? 
        and class = ? and letter_of_class = ? and subject = ?''', (homework.date[0], homework.date[1],
                                                                   homework.date[2], homework.class_of_user,
                                                                   homework.letter_of_class, homework.subject)).fetchall()
        if not bool(downloaded_homework):
            raise NoHomeworkError
        for task in downloaded_homework:
            await updater.message.reply_text(task[0], reply_markup=markup_menu)
        return ConversationHandler.END
    except NoHomeworkError:
        await updater.message.reply_text('Дз не отправлено', reply_markup=markup_menu)
        return ConversationHandler.END
    except Exception as e:
        await error(updater, context, e)
        return ConversationHandler.END


def initialization():  # Starting function
    # opening txt form
    global data
    with open('9_classes.json', encoding='utf-8') as json_file:
        data = json.load(json_file)
    with open('9_classes.json', encoding='utf-8') as json_file:
        data = json.load(json_file)[0]
    for clas in data.keys():
        for key in data[clas].keys():
            for day in data[clas][key].keys():
                data[clas][key][day] = list(map(lambda x: [KeyboardButton(x)], data[clas][key][day]))

    # Making an application of Telegram-bot
    application = Application.builder().token(BOT_TOKEN).build()

    # A handler for asking user about his class
    entry_or_change_class_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('change', change_class)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, class_asking)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_letter_of_class)]},
        fallbacks=[CommandHandler('stop', stop)]
    )

    # A handler for uploading homework to database
    uploading_homework_handler = ConversationHandler(
        entry_points=[CommandHandler('send', send)],
        states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_date)],
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, class_asking_in_dialog)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_subject)],
                4: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_homework)]},
        fallbacks=[CommandHandler('stop', stop)]
    )

    # A handler for getting homework from database
    downloading_homework_handler = ConversationHandler(
        entry_points=[CommandHandler('get', get)],
        states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_date_to_get)],
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, class_asking_in_dialog)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_subject_to_get)]},
        fallbacks=[CommandHandler('stop', stop)]
    )

    # A handler for banning people
    ban_function_handler = ConversationHandler(
        entry_points=[CommandHandler('ban', asking_for_ban)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban)]},
        fallbacks=[CommandHandler('stop', stop)]
    )

    # A handler for unbanning people
    unban_function_handler = ConversationHandler(
        entry_points=[CommandHandler('unban', asking_for_unban)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, unban)]},
        fallbacks=[CommandHandler('stop', stop)]
    )

    # A handler for printing all users database
    printing_database_handler = CommandHandler('database', print_users)

    # A handler for text messages out dialogs
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, text_answer)

    # Registration of handlers
    # ВНИМАНИЕ очень важен порядок: может съедать текстовый handler
    application.add_handler(entry_or_change_class_handler)
    application.add_handler(uploading_homework_handler)
    application.add_handler(downloading_homework_handler)
    application.add_handler(ban_function_handler)
    application.add_handler(unban_function_handler)
    application.add_handler(printing_database_handler)
    application.add_handler(text_handler)
    application.run_polling()


if __name__ == '__main__':
    homework = ActiveHomework()
    info = ChangingInformation()
    initialization()
