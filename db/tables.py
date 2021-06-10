import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

######################################################################################

BASE_TABLE = declarative_base()
class Table(BASE_TABLE):
    __abstract__ = True

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

######################################################################################

class Book(Table):
    __tablename__ = 'books'

    title = sql.Column(sql.VARCHAR(255), nullable=False)
    author = sql.Column(sql.VARCHAR(255), nullable=False)
    pages = sql.Column(sql.Integer, nullable=False)
    year = sql.Column(sql.Integer)

    # CHECKS
    __table_args__ = (
        sql.CheckConstraint('pages >= 1'),
    )

    def __init__(self, title, author, pages, year):
        self.title = title
        self.author = author
        self.pages = pages
        self.year = year


######################################################################################

class User(Table):
    __tablename__ = 'users'

    name = sql.Column(sql.VARCHAR(255), nullable=False)
    isAdmin = sql.Column(sql.Boolean, nullable=False)

    def __init__(self, name):
        self.name = name
        self.isAdmin = False

######################################################################################

class Record(Table):
    __tablename__ = 'records'

    user_id = sql.Column(sql.ForeignKey(User.id, ondelete='CASCADE'), nullable=False, index=True)
    book_id = sql.Column(sql.ForeignKey(Book.id, ondelete='CASCADE'), nullable=False, index=True)
    page = sql.Column(sql.Integer, nullable=False)
    progress = sql.Column(sql.Integer, nullable=False) # == (page / book_id.pages) * 100

    # CHECKS
    __table_args__ = (
        sql.CheckConstraint('page >= 1'),
    )

    # REFERENCES
    user = sql.orm.relationship('User', foreign_keys='Record.user_id')
    book = sql.orm.relationship('Book', foreign_keys='Record.book_id')

    def __init__(self, user_id, book_id):
        self.user_id = user_id
        self.book_id = book_id
        self.page = 1
        self.progress = 0
