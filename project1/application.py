import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import render_template, request, redirect, url_for
import hashlib
import re

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
	name = 'Guest'
	loggedIn = False
	if 'user_name' in session.keys():
		name = session['user_name']
		loggedIn = True
	return render_template("index.html", name=name, isLoggedIn=loggedIn)

user_entered_password = 'pa$$w0rd'
salt = "5gz"
db_password = user_entered_password+salt
h = hashlib.md5(db_password.encode())
print(h.hexdigest())

@app.route("/login",methods=["POST"])
def login():
	name = request.form.get("name")
	password = request.form.get("password")
	error = ""
	if not re.match("^[A-Za-z]*$", name):
		error = "Wrong user name  format. PLease use letters only"
		return render_template("index.html", error=error)
	if not re.match("^[A-Za-z0-9!@#$%^&]*$", password):
		error = "Wrong password format"
		return render_template("index.html", error=error)
	
	userExists = db.execute("SELECT id, username, password FROM users WHERE username=:user",{"user":name}).fetchone()
	
	if userExists == None:
		error = "Wrong username or password"
		return render_template("index.html", error=error)

	user_password = password+salt
	h1 = hashlib.md5(user_password.encode())
	
	if name == userExists[1] and h1.hexdigest() == userExists[2]:
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
		password = password+salt
		password = hashlib.md5(password.encode()).hexdigest()
		
		userExists = db.execute("SELECT COUNT(*) FROM users WHERE username=:user",{"user":name}).fetchone()
		
		if userExists[0] > 0:
			error = f"User name '{name}' used already. Please select new user name"
			return render_template("register.html", error=error)
		
		db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":name, "password":password})
		db.commit()
		session['user_name'] = name
		return redirect(url_for('index'))
		
	
@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for('index'))
	
	