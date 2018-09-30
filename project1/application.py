import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import render_template, request, redirect, url_for
import hashlib
import requests
import re
import json

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

Session(app)

# Set up database
engine = create_engine(app.config['DATABASE_URL'])
db = scoped_session(sessionmaker(bind=engine))

def isUserExists(username):
	user = db.execute("SELECT COUNT(*) FROM users WHERE username=:user",{"user":username}).fetchone()
	return user[0] > 0
def addUserToDB(username, password):
	db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":username, "password":password})
	db.commit()

def isUserReviewExists(user_id, book_id):
	query = "SELECT COUNT(*) FROM reviews WHERE user_id=:user_id AND book_id=:book_id"
	reviewsCount = db.execute(query,{"user_id":user_id,"book_id":book_id}).fetchone()
	return reviewsCount[0] > 0
	
def addReviewToDB(review, rating, user_id, book_id):
	query = "INSERT INTO reviews (user_id, book_id, review, rating) VALUES (:user_id, :book_id, :review, :rating)"
	db.execute(query, {"user_id":user_id, "book_id":book_id, "review":review, "rating":rating})
	
	print(f"Add review to DB: review {review}, rating {rating}, {user_id}, {book_id}")
	db.commit()
	
def getUser(username, password):
    query = "SELECT id, username, password FROM users WHERE username=:user AND password=:password"
    return db.execute(query,{"user":username,"password":password}).fetchone()
	
def getUserId(username):
    query = "SELECT id FROM users WHERE username=:user"
    return db.execute(query,{"user":username}).fetchone()[0]

def findBook(searchTerm):
	query = "SELECT * FROM books WHERE isbn LIKE :searchTerm OR title LIKE :searchTerm OR author LIKE :searchTerm"
	return db.execute(query,{"searchTerm":f"%{searchTerm}%"}).fetchall()

def getBookById(id):
	query = "SELECT * FROM books WHERE id=:id"
	return db.execute(query,{"id":id}).fetchone()

def getBookByISBN(isbn):
	query = "SELECT * FROM books WHERE isbn=:isbn"
	return db.execute(query,{"isbn":isbn}).fetchone()
	
def getBookReviews(book_id):
	query = "SELECT u.username, r.review, r.rating FROM reviews AS r, users AS u WHERE book_id=:book_id AND r.user_id = u.id"
	return db.execute(query,{"book_id":book_id}).fetchall()
	
def isUserLoggedIn():
	return 'user_name' in session.keys()
	
def encodePassword(password):
	password = password + app.config['SALT']
	password = hashlib.md5(password.encode()).hexdigest()
	return password
	
@app.route("/")
def index():
	return render_template("index.html", error=None)

@app.route("/login",methods=["POST"])
def login():
	name = request.form.get("name")
	password = request.form.get("password")

	error = ""
	if not re.match("^[A-Za-z]*$", name):
		error = "Wrong user name  format. Please use letters only"
		return render_template("index.html", error=error)
	if not re.match("^[A-Za-z0-9!@#$%^&]*$", password):
		error = "Wrong password format"
		return render_template("index.html", error=error)

	password = encodePassword(password)

	if getUser(name, password) == None:
		error = f"Wrong username or password"
		return render_template("index.html", error=error)
	else:
		session['user_name'] = name
		session['user_id'] = getUserId(name) 
	return redirect(url_for('index'))

@app.route("/register",methods=["GET","POST"])
def register():
	if request.method == "GET":
		return render_template("register.html", error=None)
	else:
		name = request.form.get("name")
		password = request.form.get("password")
		error = ""
		if not re.match("^[A-Za-z]*$", name):
			error = "Wrong user name  format. PLease use letters only"
			return render_template("register.html", error=error)
		if not re.match("^[A-Za-z0-9!@#$%^&]*$", password):
			error = "Wrong password format"
			return render_template("register.html", error=error)

		if isUserExists(name):
			error = f"User name '{name}' used already. Please select new user name or login"
			return render_template("register.html", error=error)

		password = encodePassword(password)
		addUserToDB(name, password)
		
		session['user_name'] = name
		session['user_id'] = getUserId(name)
		return redirect(url_for('index'))


@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for('index'))

	
@app.route("/search",methods=["POST"])
def find():
	searchTerm = request.form.get("term")
	books = findBook(searchTerm)
	return render_template("searchresults.html", books=books, error=None)

@app.route("/book/<int:id>")
def book(id):
	book = getBookById(id)
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": app.config['GOODREADS_KEY'], "isbns": book.isbn})
	entry = res.json()['books'][0]
	reviews = getBookReviews(id)
	error=None
	if 'book_review_add_error' in session.keys():
		error=session['book_review_add_error']
		session.pop('book_review_add_error',None)
	return render_template("book_details.html", book=book, entry=entry, reviews=reviews, error=error)
	
@app.route("/book/<int:id>/addreview",methods=["POST"])
def addReview(id):
	review = request.form.get("review")
	rating = request.form.get("rating")
	if isUserReviewExists(session['user_id'], id):
		error="User can't add more then one review for same book"
		session['book_review_add_error'] = error
		return redirect(url_for('book', id=id))
		
	addReviewToDB(review, rating, session['user_id'], id)
	return redirect(url_for('book', id=id))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404	
	
@app.route("/api/<isbn>")
def bookAPI(isbn):
	book = getBookByISBN(isbn)
	if book == None:
		return abort(404)

	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": app.config['GOODREADS_KEY'], "isbns": book.isbn})
	entry = res.json()['books'][0]
	book = dict(book)
	
	if entry != None:
		book["review_count"] = entry["work_ratings_count"]
		book["average_score"] = entry["average_rating"]
	return json.dumps(book)
	