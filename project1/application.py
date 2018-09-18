import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import render_template, request, redirect, url_for
import hashlib
import re


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

def getUser(username, password):
    query = "SELECT id, username, password FROM users WHERE username=:user AND password=:password"
    return db.execute(query,{"user":username,"password":password}).fetchone()

def findBook(searchTerm):
	query = "SELECT * FROM books WHERE isbn LIKE :searchTerm OR title LIKE :searchTerm OR author LIKE :searchTerm"
	return db.execute(query,{"searchTerm":f"%{searchTerm}%"}).fetchall()

def getBookById(id):
	query = "SELECT * FROM books WHERE id=:id"
	return db.execute(query,{"id":id}).fetchone()
	
def isUserLoggedIn():
	return 'user_name' in session.keys()
	
def encodePassword(password):
	password = password + app.config['SALT']
	password = hashlib.md5(password.encode()).hexdigest()
	return password
	
@app.route("/")
def index():
	return render_template("index.html")

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
	return redirect(url_for('index'))

@app.route("/register",methods=["GET","POST"])
def register():
	if request.method == "GET":
		return render_template("register.html")
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
		return redirect(url_for('index'))


@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for('index'))

	
@app.route("/search",methods=["POST"])
def find():
	searchTerm = request.form.get("term")
	books = findBook(searchTerm)
	return render_template("searchresults.html", books=books)

@app.route("/book/<int:id>")
def book(id):
	book = getBookById(id)
	return render_template("book_details.html", book=book)
	
	