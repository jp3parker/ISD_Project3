from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import json
import codecs

# from flaskext.mysql import MySQL
# import mysql.connector
import re
import sqlite3
import string
import os.path

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'Flask%Crud#Application'

app.permanent_session_lifetime = timedelta(minutes=1)

# Enter your database connection details below
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.sqlite")

conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

'''mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = "localhost"
app.config['MYSQL_DATABASE_PORT'] = 3308
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'flaskcrud'


# Intialize MySQL
mysql.init_app(app)
'''


def buildMovieTable():
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name == 'movies';")
    if cursor.fetchone()[0] == 0:
        with codecs.open(os.path.join(BASE_DIR, "static/movies.json"), "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        cursor.execute('CREATE TABLE IF NOT EXISTS movies(TITLE TEXT, YEAR INTEGER, CAST TEXT, GENRE TEXT);')
        for i in range(len(data) - 1, len(data) - 1001, -1):
            cast = ''
            if range(len(data[i]['cast'])):
                cast = data[i]['cast'][0]
                for actor in range(1, len(data[i]['cast']), 1):
                    cast += ", " + data[i]['cast'][actor]
            genres = ''
            if range(len(data[i]['genres'])):
                genres = data[i]['genres'][0]
                for genre in range(1, len(data[i]['genres']), 1):
                    genres += ", " + data[i]['genres'][genre]
            cursor.execute('INSERT INTO movies (TITLE, YEAR, CAST, GENRE) VALUES (?, ?, ?, ?)',
                        (data[i]['title'], data[i]['year'], cast, genres,))

        conn.commit()


@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        session.permanent = True

        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if user exists using MySQL
        # conn = mysql.connect()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))

        # Fetch one record and return result
        user = cursor.fetchone()

        # If user exists in users table in out database
        if user and check_password_hash(user[4], password):

            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['firstname'] = user[0]
            session['username'] = user[3]

            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # user doesnt exist or username/password incorrect
            msg = 'Incorrect username/password! :/'

    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('firstname', None)
    session.pop('username', None)

    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:

        # Create variables for easy access
        first = request.form['firstname']
        last = request.form['lastname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        hash = generate_password_hash(password)
        email = request.form['email']

        # Check if user exists using MySQL

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))  # SqLite Connect statement
        user = cursor.fetchone()

        # If user exists show error and validation checks
        if user:
            msg = 'Username/user already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # user doesn't exist and the form data is valid, now insert new user into users table

            # SqLite Insert Statement
            cursor.execute('INSERT INTO users (firstname, lastname, email, username, password) VALUES (?, ?, ?, ?, ?)',
                           (first, last, email, username, hash,))
            conn.commit()
            msg = 'You have successfully registered!'
            return render_template('index.html')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'

    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


@app.route('/home', methods=['GET', 'POST'])
def home():
    # Check if user is loggedin

    if request.method == "POST":
        searchBarPost = request.form["searchBar"]
        return redirect(url_for("search", searchterm=searchBarPost))

    buildMovieTable()

    genreTitles = ["Action", "Thriller", "Drama", "Comedy", "Horror", "Short", "Documentary", "Western",
                   "Adventure", "Romance", "Crime", "Historical", "Biography", "Fantasy", "Silent",
                   "Sports", "War", "Mystery", "Animated", "Science Fiction", "SuperHero", "Musical"]
    moviesByGenre = []

    for genre in genreTitles:
        search = '\'%' + genre + '%\''
        cursor.execute("SELECT DISTINCT * FROM movies WHERE GENRE LIKE %s"
                       " ORDER BY YEAR DESC LIMIT 100" % search)
        moviesByGenre.append(cursor.fetchall())

    user = '\''+session['username']+'\''
    cursor.execute("SELECT MOVIE FROM viewed WHERE USER == %s" % user)
    viewed = cursor.fetchall()
    for i in range(0, len(viewed)):
        viewed[i] = viewed[i][0]

    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', genreTitles=genreTitles, moviesByGenre=moviesByGenre, viewed=viewed)

    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/search/<searchterm>')
def search(searchterm):
    cursor.execute('CREATE TABLE IF NOT EXISTS searchHist(USER TEXT, SEARCH TEXT);')
    cursor.execute('INSERT INTO searchHist (USER, SEARCH) VALUES (?, ?)', (session['username'], searchterm,))
    searchterm = '\'%' + searchterm + '%\''
    cursor.execute("SELECT DISTINCT * FROM movies WHERE TITLE LIKE %s"
                   " ORDER BY YEAR DESC " % searchterm)
    movieResults = cursor.fetchall()
    conn.commit()

    user = '\'' + session['username'] + '\''
    cursor.execute("CREATE TABLE IF NOT EXISTS viewed(USER TEXT, MOVIE TEXT);")
    cursor.execute("SELECT MOVIE FROM viewed WHERE USER == %s" % user)
    viewed = cursor.fetchall()
    for i in range(0, len(viewed)):
        viewed[i] = viewed[i][0]

    if 'loggedin' in session:
        return render_template('search.html', movieResults=movieResults, viewed=viewed)

    return redirect(url_for('login'))


@app.route('/viewed/<movie>')
def viewed(movie):
    # cursor.execute('DROP TABLE IF EXISTS viewed;')
    cursor.execute('CREATE TABLE IF NOT EXISTS viewed(USER TEXT, MOVIE TEXT);')
    movieWQ = '\''+movie+'\''
    cursor.execute("SELECT count(*) FROM viewed WHERE MOVIE == %s;" % movieWQ)
    # print(cursor.fetchone()[0])
    if cursor.fetchone()[0] == 0:
        print("0 of these movies in viewed")
        cursor.execute('INSERT INTO viewed (USER, MOVIE) VALUES (?, ?)', (session['username'], movie,))
    else:
        print("already one of these movies in viewed")
        cursor.execute('DELETE FROM viewed WHERE MOVIE == %s;' % movieWQ)
    conn.commit()
    return redirect(url_for('home'))


@app.route('/userDetails')
def userDetails():

    user = '\''+session['username']+'\''
    cursor.execute("SELECT * FROM searchHist WHERE USER = %s" % user)
    searches = cursor.fetchall()

    return render_template('userDetails.html', searches=searches)


if __name__ == "__main__":
    app.run()
