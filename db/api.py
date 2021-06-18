import sqlalchemy as sql
import psycopg2
from datetime import datetime

#import db.tables as tables
import tables
import config


def logger(action):
    def wrapper(*args, **kwargs):
        args_ = [f'{item}' for item in args[1:]]
        kwargs_ = [f'{item[0]}={item[1]}' for item in kwargs.items()]
        arguments = ', '.join(args_ + kwargs_)
        print(f"{datetime.now()} > {args[0]}.{action.__name__}({arguments})")
        return action(*args, **kwargs)
    return wrapper


def try_except(action):
    def wrapper(*args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as error:
            print(f"___ERROR___ > {error} in {action.__name__}".replace('\n', ''))
    return wrapper


class API:

    def __init__(self, database="main.db"):
        self.database = database 
        self.create_database(database)
        self.connect(database)

    def __repr__(self):
        return f"__{self.database}__"

    @try_except
    @logger
    def connect(self, database=None):
        if (database != None):
            self.database = database
        self.engine = sql.create_engine(f'postgresql+psycopg2://{config.USERNAME}:{config.PASSWORD}@{config.HOST}:{config.PORT}/{self.database}')
        # self.engine = sql.create_engine(f'sqlite:///{self.database}')
        tables.BASE_TABLE.metadata.create_all(self.engine)
        make_session = sql.orm.sessionmaker()
        make_session.configure(bind=self.engine)
        self.session = make_session()

    @try_except
    @logger
    def save_changes(self):
        self.session.commit()

    ######################################################################################
    # PSYCOPG

    @try_except
    @logger
    def create_database(self, database):
        # Устанавливаем соединение с postgres
        connection = psycopg2.connect(user=config.USERNAME, password=config.PASSWORD, host=config.HOST, port=config.PORT)
        connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        # Создание БД
        sql_create_database = cursor.execute(f'CREATE DATABASE \"{database}\"')
        cursor.close()
        connection.close()

    @try_except
    @logger
    def delete_database(self, database):
        # Устанавливаем соединение с postgres
        connection = psycopg2.connect(user=config.USERNAME, password=config.PASSWORD, host=config.HOST, port=config.PORT)
        connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        # Удаление БД
        sql_create_database = cursor.execute(f'DROP DATABASE \"{database}\"')
        cursor.close()
        connection.close()

    ######################################################################################
    # USERS

    @try_except
    @logger
    def add_user(self, name) -> tables.User:
        user = self.get_users(name=name, first=True)
        if (user == None):
            user = tables.User(name)
            self.session.add(user)
        return user

    @try_except
    @logger
    def check_user_exist(self, name) -> bool:
        return self.session.query(sql.exists().where(tables.User.name == name)).scalar()

    @try_except
    @logger
    def get_users(self, id=None, name=None, first=False):
        if (id != None):
            return self.session.query(tables.User).where(tables.User.id == id).first()
        users = self.session.query(tables.User)
        if (name != None):
            users = users.where(tables.User.name == name)
        users.order_by(tables.User.id)
        return users.first() if first else users.all()

    @try_except
    @logger
    def delete_users(self, id=None, name=None, all=False):
        users = self.session.query(tables.User)
        if (all):
            return users.delete()
        if (id != None):
            return users.filter(tables.User.id == id).delete()
        if (name != None):
            return users.filter(tables.User.name == name).delete()

    ######################################################################################
    # BOOKS

    @try_except
    @logger
    def add_book(self, title, author, pages, year=None) -> tables.Book:
        book = self.get_books(title=title, author=author, first=True)
        if (book == None):
            book = tables.Book(title, author, pages, year)
            self.session.add(book)
        return book

    @try_except
    @logger
    def check_book_exist(self, title, author) -> bool:
        return self.session.query(sql.exists().where(tables.Book.title == title)
                                              .where(tables.Book.author == author)).scalar()

    @try_except
    @logger
    def get_books(self, id=None, title=None, author=None, first=False):
        if (id != None):
            return self.session.query(tables.Book).where(tables.Book.id == id).first()
        books = self.session.query(tables.Book)
        if (title != None):
            books = books.where(tables.Book.title == title)
        if (author != None):
            books = books.where(tables.Book.author == author)
        books = books.order_by(tables.Book.id)
        return books.first() if first else books.all()


    @try_except
    @logger
    def delete_books(self, id=None, title=None, author=None, all=False):
        books = self.session.query(tables.Book)
        if (id != None):
            return books.filter(tables.Book.id == id).delete()
        if (title != None and author != None):
            books = books.filter(tables.Book.title == title)
            books = books.filter(tables.Book.author == author)
            return books.delete()
        if (all):
            return books.delete()

    ######################################################################################
    # RECORDS

    @try_except
    @logger
    def add_record(self, user, book) -> tables.Record:
        record = self.get_records(user=user, book=book, first=True)
        if (record == None):
            record = tables.Record(user.id, book.id)
            self.session.add(record)
        return record

    @try_except
    @logger
    def get_records(self, id=None, user=None, book=None, first=False):
        if (id != None):
            return self.session.query(tables.Record).where(tables.Record.id == id).first()
        records = self.session.query(tables.Record)
        if (user != None):
            records = records.where(tables.Record.user_id == user.id)
        if (book != None):
            records = records.where(tables.Record.book_id == book.id)
        return records.first() if first else records.all()

    @try_except
    @logger
    def delete_record(self, id=None, user=None, book=None, all=False):
        records = self.session.query(tables.Record)
        if (id != None):
            return records.filter(tables.Record.id == id).delete()
        if (user != None):
            records = records.filter(tables.Record.user.id == user.id)
            if (all):
                return records.delete()
            return records.filter(tables.Record.book_id == book.id).delete()
        if (all):
            return records.delete()

    @try_except
    @logger
    def update_record(self, record, page, comment=None):
        record.page = page
        record.progress = int((record.page / record.book.pages) * 100)
        record.comment = comment


api = API()

api.add_user('andrey')
user = api.add_user('egor')
book = api.add_book('test', 'aaa', pages=132)
record = api.add_record(user, book)
api.save_changes()

api.update_record(record, 23)
api.save_changes()

api.delete_users(name='egor')
api.save_changes()

