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

from config import TOKEN
from statutes import *
from const_messages import *
from utils import book_to_string, create_inline_buttons


def start(update: Update, _: CallbackContext):
    answer = "Привет, друг! Вот тебе нерабочие команды:\n" \
             "/help\n" \
             "/search_book\n" \
             "/my_library\n" \
             "/delete_book\n" \
             "/add_book\n" \
             "/books" \

    # запрос в бд, регистрируем поль-ля
    print(update.effective_user.username)
    update.message.reply_text(answer)


# команда для отмены любой команды из списка доступных
def cancel(update: Update, _: CallbackContext):

    update.message.reply_text("Команда отменена!")

    return ConversationHandler.END


# ======= функции для работы /search_book ========
def search_books(update: Update, _: CallbackContext):

    answer = "Вы ввели команду для поиска книги. По какому полю искать книгу?\n\n" + CANCEL_MESSAGE

    keyboard = [[KeyboardButton(text=CHOICE_VALUE_NAME), KeyboardButton(text=CHOICE_VALUE_AUTHOR)]]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(answer, reply_markup=reply_markup)

    return CHOOSE_SEARCH_VALUE


def get_choice_search_value(update: Update, context: CallbackContext):

    choice_search_value = update.message.text
    context.chat_data['choice_search_value'] = choice_search_value

    if choice_search_value == CHOICE_VALUE_NAME or choice_search_value == CHOICE_VALUE_AUTHOR:
        search_value = "название" if choice_search_value == CHOICE_VALUE_NAME else "автора"

        update.message.reply_text(f'Введите {search_value}.\n' + CANCEL_MESSAGE,
                                  reply_markup=ReplyKeyboardRemove())

        return GET_SEARCH_QUERY


def get_search_query(update: Update, context: CallbackContext):
    username = update.effective_user.username
    search_query = update.message.text

    if context.chat_data['choice_search_value'] == CHOICE_VALUE_NAME:
        # запрос в БД по названию
        pass
    else:
        # запрос в БД по автору
        pass

    books = []  # книги из запроса

    if books:
        # если есть хотя бы одна книга:
        for book in books:
            book_id = book.id

            # если книга есть в моей библиотеке
            reply_markup = create_inline_buttons(username, book_id, delete=True, set_bookmark=True)

            # иначе
            # reply_markup = create_inline_buttons(username, book_id, add2library=True)
            update.message.reply_text(book_to_string(book),
                                      reply_markup=reply_markup)

    # если запрос в БД ничего не выдал
    else:
        answer = "Поиск не дал никаких результатов."
        update.message.reply_text(answer)

    return ConversationHandler.END
# ================================================


# ========= функция для работы /books ===========
def show_books(update: Update, _: CallbackContext):
    # функция для вывода всех книг, которые есть глобально

    # запрос в БД
    books = []  # книги из запроса

    answer = ""
    for book in books:
        answer += book_to_string(book)

    update.message.reply_text(text=answer)
# ==================================================


# ======== функция для работы /my_library ==========
def my_library(update: Update, _: CallbackContext):

    # запрос в БД
    books = []  # книги из запроса

    if books:
        for book in books:
            answer = book_to_string()

            book_id = book.id
            username = update.effective_user.username

            reply_markup = create_inline_buttons(username, book_id, delete=True, set_bookmark=True)

            update.message.reply_text(answer, reply_markup=reply_markup)
    else:
        answer = "В вашей библиотеке нет ни одной книги :("
        update.message.reply_text(answer)

# ===================================================


# ========= функция для работа /add_book ============
def add_book(update: Update, context: CallbackContext):
    answer = "Введите данные для книги в формате, как ниже:\n\n" \
             "Название\n" \
             "Автор (Фамилия Имя Отчество)\n" \
             "Год написания\n" \
             "Количество страниц\n\n" + CANCEL_MESSAGE

    update.message.reply_text(text=answer)

    return GET_BOOK_DATA


def get_book_data(update: Update, context: CallbackContext):
    data = update.message.text

    parsed_data = data.split("\n")

    if len(parsed_data) == 4:
        name, author, year, pages = parsed_data

        if len(author.split()) == 3:

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

            # запрос в бд о добавлении книги в глобал
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
        set_bookmark()

    # update.callback_query.message.reply_text(answer)
    # print(type(update.callback_query.message))
# ====================================================


def delete_book_from_library(query: CallbackQuery, username: str, book_id: int):
    # запрос в БД
    query.edit_message_text(text=f"Книга с ID= {book_id} удалена из вашей библиотеки")


def add_book_to_library(query: CallbackQuery, username: str, book_id: int):
    # запрос в БД, добавить книгу в библиотеку
    query.edit_message_text(text=f"Книга с ID= {book_id} добавлена в вашу библиотеку")


def set_bookmark():
    pass


def for_test(update: Update, context: CallbackContext):
    update.message.reply_text(text="kzkfkzkdsasd", reply_markup=create_inline_buttons("asdad", 12, add2library=True))


if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    search_book_handler = ConversationHandler(
        entry_points=[CommandHandler('search_book', search_books)],

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

    inline_buttons_handler = CallbackQueryHandler(callback=callback_inline_buttons_handler)
    dispatcher.add_handler(inline_buttons_handler)

    test_handler = CommandHandler('test', for_test)
    dispatcher.add_handler(test_handler)

    updater.start_polling()
