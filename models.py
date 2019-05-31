import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db= SQLAlchemy()


class Book(db.Model):
    __tablename__ = 'books'
    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)

    def add_account(username, password, first_name, last_name):
        a = Account(username=username, password=password, first_name=first_name, last_name=last_name)
        db.session.add(a)
        db.session.commit()


class Review(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.Integer, primary_key=True)
    book_isbn = db.Column(db.Integer, db.ForeignKey('books.isbn'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('accounts'), nullable=False)
    rating = db.Column(db.Numeric, nullable=False)
    review = db.Column(db.String(300), nullable=False)
