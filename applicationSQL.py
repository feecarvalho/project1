from flask import Flask, request, render_template, jsonify, session
from models import *
from flask_session import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker
import os
import hashlib
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://teykjyfsvqcamv:f982273d2058ffd4fccc4eba198ca702ac67ee7f42ff26f11c8653ba41f5cbcd@ec2-54-197-239-115.compute-1.amazonaws.com:5432/d1rcjij2006gm5'
app.config['SECRET_KEY'] = 'pao_de_mel'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
db.init_app(app)


@app.route('/')
def index():
    if session.get('logged_in'):
        session['displayname']
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    message = ''
    if session.get('logged_in'):
        return render_template('index.html', message='You already logged in!')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username and password match
        connection = Account.query.filter(and_(Account.username == username, Account.password == password)).all()
        if connection != []:
            session['logged_in'] = True
            show_name = Account.query.filter(username == username).all()
            session['displayname'] = show_name[0].first_name
            session['username'] = show_name[0].id
            return render_template('index.html', message='Login successfull.')
        else:
            message='Username or password incorrect!'
    return render_template('login.html', message=message)


@app.route('/register', methods=['POST', 'GET'])
def register():
    message = ''
    if session.get('logged_in'):
        return render_template('index.html', message='You are already registered!')
    if request.method == 'POST':
        username = request.form.get('username')
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')

        # Check if password match
        if pass1 != pass2 or pass1 is None or pass2 is None:
            return render_template('error.html', message='Your password is invalid or doesnt match')
        password = pass1
        # Check if username is available
        if Account.query.filter(Account.username == username).all() != []:
            return render_template('error.html', message='Username already in use')
        Account.add_account(username, password, first_name, last_name)
        return render_template('login.html', message='New account created successfully! Please login to start using SNK Bookstore!')
    return render_template('register.html', message=message)



@app.route('/logout')
def logout():
    session['logged_in'] = False
    session['username'] = ''
    return render_template('logout.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    message = None
    if not session['logged_in']:
        message='Please login first!'
        return render_template('book.html', message=message)
    if request.method == 'POST':
        info_type = request.form.get('book_tags')
        book_info = request.form.get('search_value').lower()

        if info_type != 'year':
            sql = f'''SELECT * FROM books WHERE LOWER({info_type}) LIKE '%{book_info}%' ORDER BY title ASC'''
        elif info_type == 'year':
            sql = f'''SELECT * FROM books WHERE {info_type} = {book_info} ORDER BY title ASC'''

        if db.execute(sql).rowcount == 0:
            message = 'No results found!'
            return render_template('book.html', message=message)
        else:
            books_result = db.execute(sql).fetchall()
            return render_template('book.html', books_result=books_result)
    return render_template('search.html')

@app.route('/book/<string:isbn_id>')
def isbn(isbn_id):
    sel_book = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn_id}).fetchone()
    user_id = session['username']
    review_list = db.execute('SELECT rating, review, first_name, last_name FROM reviews INNER JOIN accounts ON accounts.id = user_id AND book_isbn = :isbn_id', {'isbn_id': isbn_id}).fetchall()
    res = requests.get('https://www.goodreads.com/book/review_counts.json', params={'key': 'wstERZo4jV9Or7FSG2sIQ', 'isbns': sel_book['isbn']})
    if res is not None:
        print(res.json())
    return render_template('book.html', sel_book=sel_book, review_list=review_list, res=res)

@app.route('/review/<string:isbn_id>', methods=['POST'])
def review(isbn_id):
    review = request.form.get('comment')
    book_isbn = isbn_id
    rating = request.form.get('star').split('/')
    rating = float(rating[0])
    user_id = session['username']
    if request.method == 'POST' and review != '':
        db.execute('INSERT INTO reviews (book_isbn, rating, review, user_id) VALUES (:book_isbn, :rating, :review, :user_id)', {'book_isbn': book_isbn, 'rating': rating, 'review': review, 'user_id': user_id})
        db.commit()
        message = 'Review submited successfully!'
        return render_template('review.html', message=message, isbn_id=isbn_id)
    return render_template('book.html')

@app.route('/api/<isbn>')
def api(isbn):
    if db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn}).rowcount == 0:
        return render_template('error.html', message='404 ERROR!')
    isbn_found = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn}).fetchone()
    review_count = db.execute('SELECT rating FROM reviews WHERE book_isbn = :isbn', {'isbn': isbn_found.isbn}).rowcount
    average_rating = db.execute('SELECT AVG(rating) FROM reviews WHERE book_isbn = :isbn', {'isbn': isbn_found.isbn}).fetchone()
    if average_rating == float:
        average_rating = float(average_rating[0])
    else:
        average_rating = 0
    return render_template('api.html', isbn_found=isbn_found, review_count=review_count, average_rating=average_rating)
