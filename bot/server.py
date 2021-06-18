from telegram.ext import (Updater,
                          Dispatcher,
                          Filters,
                          CommandHandler,
                          CallbackContext,
                          ConversationHandler,
                          MessageHandler,
                          CallbackQueryHandler,
                          )

from telegram import (Bot, Message, CallbackQuery,
                      ReplyKeyboardRemove, ReplyKeyboardMarkup,
                      InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton,
                      Update,
                      )

from config import TOKEN, USERNAME_ADMIN
from statutes import *
from const_messages import *
from utils import book_to_string, create_inline_buttons

import db.api as api


# ======== проверка работы БД ===========
def is_database_created(func):
    def wrapper(*args, **kwargs):
        update, context = args
        username = update.effective_user.username
        if api.api is None and username == USERNAME_ADMIN:
            answer = "Здравствуйте, Андрей, вы являетесь администратором этого бота, создайте базу данных для" \
                     "корректной работы бота.\n\n" \
                     "/create_database - cоздать базу данных\n" \
                     "/delete_database - удалить базу данных\n"
            update.message.reply_text(text=answer)
        elif api.api is None:
            answer = "База данных не создана, бот не работает."
            update.message.reply_text(text=answer)

        elif api.api is not None:
            func(*args, **kwargs)

    return wrapper
# ========================================


# ===== функция для работы команды /start =====
@is_database_created
def start(update: Update, _: CallbackContext):
    answer = "Привет, друг! Мои команды:\n" \
             "/help\n" \
             "/search\n" \
             "/my_library\n" \
             "/add_book\n" \
             "/books" \

    # запрос в бд, регистрируем поль-ля
    user = api.api.add_user(update.effective_user.username)
    api.api.save_changes()

    update.message.reply_text(answer)
# =============================================


# ===== команда для отмены любой команды из списка доступных =====
def cancel(update: Update, _: CallbackContext):

    update.message.reply_text("Команда отменена!")

    return ConversationHandler.END
# ==============================================


# ==== функция для работы команды /create_database ====
def create_database(update: Update, _: CallbackContext):
    if update.effective_user.username == USERNAME_ADMIN:
        api.api = api.API()
        api.api.add_user(name=USERNAME_ADMIN, isAdmin=True)
        update.message.reply_text(text="База данных создана, бот работает корректно.")
    else:
        update.message.reply_text(text="У вас нет прав для этой команды.")
# =================================================


# ==== функция для работы команды /delete_database ====
def delete_database(update: Update, _: CallbackContext):

    if update.effective_user.username == USERNAME_ADMIN:
        api.api.delete_database(api.api.database)
        api.api = None

        update.message.reply_text(text="База данных удалена, бот больше не работает.")
    else:
        update.message.reply_text(text="У вас нет прав для этой команды.")
# =================================================


# ======= функции для работы /search_book ========
@is_database_created
def search_books(update: Update, _: CallbackContext):

    answer = "Вы ввели команду для поиска книги. По какому полю искать книгу?\n\n" + CANCEL_MESSAGE

    keyboard = [
                [KeyboardButton(text=CHOICE_VALUE_NAME), KeyboardButton(text=CHOICE_VALUE_AUTHOR)],
                [KeyboardButton(text=CHOICE_VALUE_NAME_AND_AUTHOR)]
               ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(answer, reply_markup=reply_markup)

    return CHOOSE_SEARCH_VALUE


def get_choice_search_value(update: Update, context: CallbackContext):

    choice_search_value = update.message.text
    context.chat_data['choice_search_value'] = choice_search_value

    if choice_search_value == CHOICE_VALUE_NAME or choice_search_value == CHOICE_VALUE_AUTHOR:
        search_value = "название" if choice_search_value == CHOICE_VALUE_NAME else "автора"

        answer = f'Введите {search_value}.\n'
        update.message.reply_text(text=answer + CANCEL_MESSAGE,
                                  reply_markup=ReplyKeyboardRemove())
    else:
        answer = f'Введите название и автора в формате:\n' \
                 f'Название\n' \
                 f'Автор\n'
        update.message.reply_text(text=answer + CANCEL_MESSAGE,
                                  reply_markup=ReplyKeyboardRemove())
        return GET_SEARCH_QUERY


def get_search_query(update: Update, context: CallbackContext):
    username = update.effective_user.username
    search_query = update.message.text

    user = api.api.get_users(name=username, first=True)

    books = []  # книги из запроса
    if context.chat_data['choice_search_value'] == CHOICE_VALUE_NAME:
        books = api.api.get_books(title=search_query)
    elif context.chat_data['choice_search_value'] == CHOICE_VALUE_AUTHOR:
        books = api.api.get_books(author=search_query)
    else:
        title, author = search_query.split('\n')
        books = api.api.get_books(author=author, title=title)

    if books:
        # если есть хотя бы одна книга:
        for book in books:
            book_id = book.id

            if api.api.get_records(book=book, user=user, first=True) is not None:
                # если книга есть в моей библиотеке
                reply_markup = create_inline_buttons(username, book_id, delete=True, set_bookmark=True)
            # иначе
            else:
                reply_markup = create_inline_buttons(username, book_id, add2library=True)

            update.message.reply_text(book_to_string(book),
                                      reply_markup=reply_markup)

    # если запрос в БД ничего не выдал
    else:
        answer = "Поиск не дал никаких результатов."
        update.message.reply_text(answer)

    return ConversationHandler.END
# ================================================


# ========= функция для работы /books ===========
@is_database_created
def show_books(update: Update, _: CallbackContext):
    # функция для вывода всех книг, которые есть глобально

    # запрос в БД
    books = api.api.get_books()  # книги из запроса

    answer = ""
    for book in books:
        answer += book_to_string(book)

    update.message.reply_text(text=answer)
# ==================================================


# ======== функция для работы /my_library ==========
@is_database_created
def my_library(update: Update, _: CallbackContext):
    # запрос в бд
    user = api.api.get_users(update.effective_user.username)
    records = api.api.get_records(user=user)

    if records:
        for record in records:
            answer = book_to_string(record.book, bookmark=record.page, progress=record.progress)

            book_id = record.book.id
            username = update.effective_user.username

            reply_markup = create_inline_buttons(username, book_id, delete=True, set_bookmark=True)

            update.message.reply_text(answer, reply_markup=reply_markup)
    else:
        answer = "В вашей библиотеке нет ни одной книги :("
        update.message.reply_text(answer)

# ===================================================


# ========= функция для работа /add_book ============
@is_database_created
def add_book(update: Update, context: CallbackContext):
    answer = "Введите данные для книги в формате, как ниже:\n\n" \
             "Название\n" \
             "Автор (информация о нем, Фамилия Имя)\n" \
             "Год написания\n" \
             "Количество страниц\n\n" + CANCEL_MESSAGE

    update.message.reply_text(text=answer)

    return GET_BOOK_DATA


def get_book_data(update: Update, context: CallbackContext):
    data = update.message.text

    parsed_data = data.split("\n")

    if len(parsed_data) == 4:
        name, author, year, pages = parsed_data

        if len(author.split()) >= 2:

            try:
                year = int(year)
            except ValueError:
                update.message.reply_text(text="Неверный формат данных об годе выпуска.\n\nВернули вас в главное меню.")
                return ConversationHandler.END

            try:
                pages = int(pages)
            except ValueError:
                update.message.reply_text(text="Неверный формат данных об годе выпуска.\n\nВернули вас в главное меню.")
                return ConversationHandler.END

            api.api.add_book(title=name, author=author, pages=pages, year=year)
            api.api.save_changes()

            update.message.reply_text(text="Вы успешно добавили книгу!")
        else:
            update.message.reply_text(text="Неверный формат данных об авторе.\n\nВернули вас в главное меню.")
    else:
        update.message.reply_text(text="Вы ввели мало данных.\n\nВернули вас в главное меню.")

    return ConversationHandler.END
# ======================================================


# ========= функция для распределения команд из инлайн кнопок =============
def callback_inline_buttons_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    command, username, book_id = query.data.split("|")

    answer = f'{command} {username} {book_id}'

    if command == COMMAND_ADD:
        add_book_to_library(query, username, int(book_id))

    if command == COMMAND_DELETE:
        delete_book_from_library(query, username, int(book_id))

    if command == COMMAND_SET_BOOKMARK:
        set_bookmark(query, context, book_id)

    # update.callback_query.message.reply_text(answer)
    # print(type(update.callback_query.message))
# ====================================================


def delete_book_from_library(query: CallbackQuery, username: str, book_id: int):
    # запрос в БД
    user = api.api.get_users(name=username, first=True)
    book = api.api.get_books(id=book_id, first=True)

    api.api.delete_record(user=user, book=book)
    api.api.save_changes()

    query.edit_message_text(text=f"Книга с ID= {book_id} удалена из вашей библиотеки")


def add_book_to_library(query: CallbackQuery, username: str, book_id: int):
    # запрос в БД, добавить книгу в библиотеку
    user = api.api.get_users(name=username, first=True)
    book = api.api.get_books(id=book_id)
    print(user, book)

    api.api.add_record(user=user, book=book)
    api.api.save_changes()

    query.edit_message_text(text=f"Книга с ID= {book_id} добавлена в вашу библиотеку")


def set_bookmark(query: CallbackQuery, context: CallbackContext, book_id):
    context.chat_data['set_bookmark'] = True
    context.chat_data['book_id'] = book_id

    query.message.reply_text(text="Введите номер страницы, на который вы остановились.")


def get_page(update: Update, context: CallbackContext):
    is_set_bookmark_command = context.chat_data.get('set_bookmark', None)
    if is_set_bookmark_command:
        try:
            new_page = int(update.message.text)
        except ValueError:
            update.message.reply_text(text="Вы ввели не число.\n\nВернули вас в главное меню.")

        book_id = context.chat_data['book_id']

        username = update.effective_user.username
        # user = api.api.get_users(name=username, first=True)
        # book = api.api.get_books(id=book_id)
        #
        # record = api.api.get_records(user=user, book=book, first=True)

        # api.api.update_record(record=record, int(new_page))
        answer = "Номер страницы, на которой вы остановились, обновлена.\n\n" #+ \
                 # book_to_string(book, bookmark=record.page, progress=record.progress)
        update.message.reply_text(text=answer,
                                  reply_markup=create_inline_buttons(username, book_id, delete=True, set_bookmark=True))

# @is_database_created
def for_test(update: Update, context: CallbackContext):
    update.message.reply_text(text="kzkfkzkdsasd", reply_markup=create_inline_buttons("asdad", 12, set_bookmark=True))


if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    search_book_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search_books)],

        states={
            CHOOSE_SEARCH_VALUE: [MessageHandler(Filters.text & ~Filters.command, get_choice_search_value)],

            GET_SEARCH_QUERY: [MessageHandler(Filters.text & ~Filters.command, get_search_query)]
        },

        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dispatcher.add_handler(search_book_handler)

    add_book_handler = ConversationHandler(
        entry_points=[CommandHandler('add_book', add_book)],

        states={
            GET_BOOK_DATA: [MessageHandler(Filters.text & ~Filters.command, get_book_data)],
        },

        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dispatcher.add_handler(add_book_handler)

    show_books_handler = CommandHandler('books', show_books)
    dispatcher.add_handler(show_books_handler)

    my_library_handler = CommandHandler('my_library', my_library)
    dispatcher.add_handler(my_library_handler)

    create_database_handler = CommandHandler('create_database', create_database)
    dispatcher.add_handler(create_database_handler)

    delete_database_handler = CommandHandler('delete_database', delete_database)
    dispatcher.add_handler(delete_database_handler)

    inline_buttons_handler = CallbackQueryHandler(callback=callback_inline_buttons_handler)
    dispatcher.add_handler(inline_buttons_handler)

    set_bookmark_handler = MessageHandler(Filters.text & ~Filters.command, get_page)
    dispatcher.add_handler(set_bookmark_handler)

    test_handler = CommandHandler('test', for_test)
    dispatcher.add_handler(test_handler)

    updater.start_polling()
