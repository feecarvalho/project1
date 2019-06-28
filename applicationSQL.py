from flask import Flask, request, render_template, jsonify, session
from models import *
from sqlalchemy import exc
from sqlalchemy import func
from flask_session import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker
import os
import hashlib
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://teykjyfsvqcamv:f982273d2058ffd4fccc4eba198ca702ac67ee7f42ff26f11c8653ba41f5cbcd@ec2-54-197-239-115.compute-1.amazonaws.com:5432/d1rcjij2006gm5'
app.config['SECRET_KEY'] = 'a%@ddj$sjqozm#2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
db.init_app(app)


@app.route('/')
def index():
    if session['logged_in']:
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
        if connection:
            session['logged_in'] = True
            show_name = Account.query.filter(Account.username == username).all()
            session['displayname'] = show_name[0].first_name
            session['username'] = show_name[0].id
            return render_template('index.html', message='Login successful.')
        else:
            message='Username or password incorrect!'
    return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    session['logged_in'] = False
    session['displayname'] = ''
    session['username'] = ''
    return render_template('logout.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
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

        # Check if username is available
        if Account.query.filter(Account.username == username).all() is None:
            return render_template('error.html', message='Username already in use')

        password = pass1

        # Insert new account to database
        account = Account(username=username, password=password, first_name=first_name, last_name=last_name)
        db.session.add(account)
        db.session.commit()
        return render_template('login.html', message='New account created successfully! Please login to start using SNK Bookstore!')
    return render_template('register.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if not session['logged_in']:
        return render_template('book.html', message='Please login first!')

    if request.method == 'POST':
        info_type = request.form.get('book_tags').lower()
        book_info = request.form.get('search_value').lower()
        if info_type != 'year':
            book_info = f'%{book_info.lower()}%'
            books_result = Book.query.order_by(Book.title.asc()).filter(getattr(Book, info_type).ilike(book_info)).all()
        else:
            books_result = Book.query.order_by(Book.title.asc()).filter(Book.year == int(book_info)).all()
        if not books_result:
            return render_template('search.html', message="No books found.")
        return render_template('book.html', books_result=books_result)
    return render_template('search.html')


@app.route('/book/<string:isbn_id>')
def isbn(isbn_id):
    sel_book = Book.query.filter(Book.isbn == isbn_id).all()
    review_list = db.session.query(Review, Account).filter(Review.book_isbn == isbn_id).all()
    print(f'----------------{review_list}----------------')
    res = requests.get('https://www.goodreads.com/book/review_counts.json', params={'key': 'wstERZo4jV9Or7FSG2sIQ', 'isbns': isbn_id})

    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    print(data)
    avg_rating = data["books"][0]["average_rating"]
    print(f'=================={avg_rating}==================')
    return render_template('book.html', sel_book=sel_book, review_list=review_list, res=avg_rating)


@app.route('/review/<string:isbn_id>', methods=['POST'])
def review(isbn_id):
    review = request.form.get('comment')
    rating = request.form.get('star').split('/')
    rating = float(rating[0])
    user_id = session['username']
    if request.method == 'POST' and review != '':

        # Check if the user hasn't sent a review already.
        try:
            rev = Review(book_isbn=isbn_id, user_id=user_id, rating=rating, review=review)
            db.session.add(rev)
            db.session.commit()
        except exc.IntegrityError:
            return render_template('error.html', message='You have already submitted a review for this book!')

        return render_template('review.html', message='Review submitted successfully!', isbn_id=isbn_id)
    return render_template('book.html')


@app.route('/api/book/<isbn>')
def api(isbn):
    ''' Return JSON details about a single book. '''

    # Make sure the book exist.
    book = Book.query.get(isbn)

    if book is None:
        return jsonify({"error": "Invalid book"}), 422

    review_count = len(Review.query.filter(Review.book_isbn == isbn).all())

    if review_count is None:
        return jsonify({"error": "No review for this book."})

    average_score = str(db.session.query(func.avg(Review.rating)).all()).split("'")
    average_score = float(average_score[1])

    return jsonify({
        "isbn": book.isbn,
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "average_score": average_score,
        "review_count": review_count
    })
