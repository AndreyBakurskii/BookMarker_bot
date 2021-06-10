from telegram.ext import (Updater,
                          Dispatcher,
                          Filters,
                          CommandHandler,
                          CallbackContext,
                          ConversationHandler,
                          MessageHandler
                          )

from telegram import (Bot,
                      ReplyKeyboardRemove, ReplyKeyboardMarkup,
                      KeyboardButton,
                      Update,
                      )

from config import TOKEN
from statutes import *
from const_messages import *


def start(update: Update, _: CallbackContext):
    answer = "Привет, друг! Вот тебе нерабочие команды:\n/help\n/search_book\n/my_library\n/set_bookmaker\n" \
             "/delete_book\n/add_book\n"

    update.message.reply_text(answer)


def cancel(update: Update, _: CallbackContext):

    update.message.reply_text("Команда отменена!")

    return ConversationHandler.END


def search_book(update: Update, _: CallbackContext):

    answer = "Вы ввели команду для поиска книги. По какому полю искать книгу?\n" \
             "Если нужно искать по названию, введите 1.\n" \
             "Если нужно искать по автору, введите 2.\n" \
             "\n" + CANCEL_MESSAGE

    update.message.reply_text(answer)

    return CHOOSE_SEARCH_VALUE


def choose_search_value(update: Update, context: CallbackContext):

    choice_search_value = int(update.message.text)
    context.chat_data['choice_search_value'] = choice_search_value

    if choice_search_value == 1 or choice_search_value == 2:
        search_value = "название" if choice_search_value == 1 else "автора"

        update.message.reply_text(f'Введите {search_value}.\n' + CANCEL_MESSAGE)

        return GET_SEARCH_QUERY

    else:
        answer = f'Вы ввели недопустимое сообщение :(\n\n' \
                 f'Вернули Вас в главное меню.'

        update.message.reply_text(answer)

        return ConversationHandler.END


def get_search_query(update: Update, context: CallbackContext):

    search_query = update.message.text
    # запрос в БД

    print(context.chat_data.get('choice_search_value'))

    # если есть хотя бы одна книга:
    answer1 = f'Book name: \n' \
              f'Author: \n' \
              f'ID: \n' \
              f'Bookmark: \n' \
              f'--------------\n'

    update.message.reply_text(answer1)

    # если запрос в БД ничего не выдал

    answer2 = "Поиск не дал никаких результатов.\n\n" \
              "Если хотите добавить новую книгу введите /add_book"

    update.message.reply_text(answer2)

    return ConversationHandler.END


def my_library(update: Update, _: CallbackContext):

    # запрос в БД
    answer = f'Book name: \n' \
              f'Author: \n' \
              f'ID: \n' \
              f'Bookmark: \n' \
              f'--------------\n'

    update.message.reply_text(answer)


if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    search_book_handler = ConversationHandler(
        entry_points=[CommandHandler('search_book', search_book)],

        states={
            CHOOSE_SEARCH_VALUE: [MessageHandler(Filters.text & ~Filters.command, choose_search_value)],

            GET_SEARCH_QUERY: [MessageHandler(Filters.text & ~Filters.command, get_search_query)]
        },

        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dispatcher.add_handler(search_book_handler)

    my_library_handler = CommandHandler('my_library', my_library)
    dispatcher.add_handler(my_library_handler)


    updater.start_polling()
