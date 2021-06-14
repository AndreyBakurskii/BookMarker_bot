from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def book_to_string(book=None) -> str:
    # answer = f'Book name: {}\n' \
    #          f'Author: {}\n' \
    #          f'ID: {}\n' \
    #          f'Bookmark: {}\n' \
    #          f'--------------\n'

    answer = f'Book name: Война и мир\n' \
             f'Author: Толстой Л.Н.\n' \
             f'ID: 1\n' \
             f'Bookmark: 0\n' \
             f'--------------\n'
    return answer


def create_inline_buttons(username, book_id, delete=False, set_bookmark=False, add2library=False):
    row = []

    if delete:
        delete_button = InlineKeyboardButton(text="Удалить", callback_data=f'delete|{username}|{book_id}')
        row.append(delete_button)

    if set_bookmark:
        set_bookmark_button = InlineKeyboardButton(text="Изменить закладку",
                                                   callback_data=f'setBookmark|{username}|{book_id}')
        row.append(set_bookmark_button)
    if add2library:
        add2library_button = InlineKeyboardButton(text="Добавить в мою библиотеку",
                                                  callback_data=f'addBook2Library|{username}|{book_id}')
        row.append(add2library_button)

    reply_markup = InlineKeyboardMarkup([row])

    return reply_markup
