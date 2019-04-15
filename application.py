from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import pbkdf2_sha256
import os
import hashlib
import requests

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# API Goodreads
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "wstERZo4jV9Or7FSG2sIQ", "isbns": "9781632168146"})
print(res.json())

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    return render_template("index.html", )


@app.route("/register", methods=['POST', 'GET'])
def register():
    message = None
    if request.method == "POST":
        username = request.form.get("username")
        pass1 = request.form.get("pass1")
        pass2 = request.form.get("pass2")
        if pass1 != pass2 or pass1 is None or pass2 is None:
            message = "Your password is invalid or doesn't match".upper()
            return render_template("register.html", message=message)
        password = pass1
        usr = db.execute("SELECT username FROM accounts WHERE username = :username", {"username": username}).fetchone()
        if usr != None:
            message = "Username already in use".upper()
            return render_template('register.html', message=message)
        db.execute("INSERT INTO accounts (username, password) VALUES (:username, :password)", {"username": username, "password": password})
        db.commit()
    message = "New account created successfully!"
    return render_template("register.html", message=message)


@app.route("/login", methods=['POST', 'GET'])
def login():
    message = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        connection = db.execute("SELECT * FROM accounts WHERE username = :username AND password = :password", {"username": username, "password": password}).fetchall()
        if connection[0] == username and connection[1] == password:
            message = "Login successfull"
            return render_template("index.html", message=message)
    message = "Username or password incorrect!"
    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    return render_template("logout.html")
