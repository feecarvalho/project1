from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
import hashlib
import requests

app = Flask(__name__)
#app.config['DATABASE_URL'] = 'postgres://teykjyfsvqcamv:f982273d2058ffd4fccc4eba198ca702ac67ee7f42ff26f11c8653ba41f5cbcd@ec2-54-197-239-115.compute-1.amazonaws.com:5432/d1rcjij2006gm5'

# Set Alchemy up database
engine = create_engine('postgres://teykjyfsvqcamv:f982273d2058ffd4fccc4eba198ca702ac67ee7f42ff26f11c8653ba41f5cbcd@ec2-54-197-239-115.compute-1.amazonaws.com:5432/d1rcjij2006gm5')
db = scoped_session(sessionmaker(bind=engine))

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    if session.get('logged_in'):
        show_name = db.execute("SELECT first_name FROM accounts WHERE id = :id", {"id": session['username']}).fetchone()
        session['displayname'] = str(show_name[0])
        return render_template("index.html", status="loggedin")
    else:
        return render_template("index.html")


@app.route("/register", methods=['POST', 'GET'])
def register():
    message = ""
    if session.get('logged_in'):
        # session['logged_in'] = True
        return render_template("index.html", message="You are already registered!")
    if request.method == "POST":
        username = request.form.get("username")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        pass1 = request.form.get("pass1")
        pass2 = request.form.get("pass2")
        if pass1 != pass2 or pass1 is None or pass2 is None:
            message = "Your password is invalid or doesn't match"
            return render_template("register.html", message=message)
        else:
            password = pass1
        usr = db.execute("SELECT username FROM accounts WHERE username = :username", {"username": username}).fetchone()
        if usr != None:
            message = "Username already in use"
            return render_template('register.html', message=message)
        else:
            db.execute("INSERT INTO accounts (username, password, first_name, last_name) VALUES (:username, :password, :firstname, :lastname)", {"username": username, "password": password, "firstname": firstname, "lastname": lastname})
        db.commit()
        message = "New account created successfully! Please login to start using SNK Bookstore!"
        return render_template("login.html", message=message)
    return render_template("register.html", message=message)


@app.route("/login", methods=['POST', 'GET'])
def login():
    message = None
    if session.get('logged_in'):
        session['logged_in'] = True
        return render_template("index.html", message="You already logged in!")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        connection = db.execute("SELECT * FROM accounts WHERE username = :username AND password = :password", {"username": username, "password": password}).fetchone()
        if connection is not None:
            message = "Login successfull"
            session['logged_in'] = True
            show_name = db.execute("SELECT id, first_name FROM accounts WHERE username = :username", {"username": username}).fetchone()
            session['displayname'] = str(show_name[1])
            session['username'] = str(show_name[0])
            return render_template("index.html", message=message, status="loggedin")
        else:
            return render_template("login.html", message="Username or password incorrect!", status="loggedout")
    return render_template("login.html", status="loggedout")


@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['username'] = ''
    return render_template("logout.html", status="loggedout")


@app.route("/search", methods=['GET', 'POST'])
def search():
    message = None
    if not session['logged_in']:
        message='Please login first!'
        return render_template('book.html', message=message)
    if request.method == 'POST':
        info_type = request.form.get('book_tags')
        book_info = request.form.get('search_value').lower()

        if info_type != 'year':
            sql = f"""SELECT * FROM books WHERE LOWER({info_type}) LIKE '%{book_info}%' ORDER BY title ASC"""
        elif info_type == 'year':
            sql = f"""SELECT * FROM books WHERE {info_type} = {book_info} ORDER BY title ASC"""

        if db.execute(sql).rowcount == 0:
            message = 'No results found!'
            return render_template('book.html', message=message)
        else:
            books_result = db.execute(sql).fetchall()
            return render_template('book.html', books_result=books_result)
    return render_template('search.html')

@app.route('/book/<string:isbn_id>')
def isbn(isbn_id):
    sel_book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn_id}).fetchone()
    user_id = session['username']
    review_list = db.execute("SELECT rating, review, first_name, last_name FROM reviews INNER JOIN accounts ON accounts.id = user_id AND book_isbn = :isbn_id", {"isbn_id": isbn_id}).fetchall()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "wstERZo4jV9Or7FSG2sIQ", "isbns": sel_book['isbn']})
    if res is not None:
        print(res.json())
    return render_template('book.html', sel_book=sel_book, review_list=review_list, res=res)

@app.route('/review/<string:isbn_id>', methods=["POST"])
def review(isbn_id):
    review = request.form.get('comment')
    book_isbn = isbn_id
    rating = request.form.get('star').split('/')
    rating = float(rating[0])
    user_id = session['username']
    if request.method == "POST" and review != "":
        db.execute("INSERT INTO reviews (book_isbn, rating, review, user_id) VALUES (:book_isbn, :rating, :review, :user_id)", {"book_isbn": book_isbn, "rating": rating, "review": review, "user_id": user_id})
        db.commit()
        message = 'Review submited successfully!'
        return render_template('review.html', message=message, isbn_id=isbn_id)
    return render_template('book.html')

@app.route('/api/<isbn>')
def api(isbn):
    if db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount == 0:
        return render_template('error.html', message="404 ERROR!")
    isbn_found = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    review_count = db.execute("SELECT rating FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn_found.isbn}).rowcount
    average_rating = db.execute("SELECT AVG(rating) FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn_found.isbn}).fetchone()
    if average_rating == float:
        average_rating = float(average_rating[0])
    else:
        average_rating = 0
    return render_template('api.html', isbn_found=isbn_found, review_count=review_count, average_rating=average_rating)
