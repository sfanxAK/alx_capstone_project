from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import datetime
import MySQLdb

# create Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key" 

# configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'RecipeLab_database'
mysql = MySQL(app)

# ------------- index --------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/Recipes')
def Recipes():
    return render_template('Recipes.html')


# ------------ register --------------

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]

            conn = MySQLdb.connect(host='localhost', user='root', password='', database='RecipeLab_database')

            if conn:
                cur = conn.cursor()

                # Check if username or email already exists
                cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cur.fetchone()

                if existing_user:
                    # Username or email already exists, render registration template with error message
                    return render_template("register.html", message="Username or email already exists!")

                # Insert the new user if username and email are unique
                cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for("login"))  #return to the login page after successful registration
        except Exception as e:
            return render_template("error.html", error=str(e))

    return render_template('register.html')

# -------------- login -----------------

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = MySQLdb.connect(host='localhost', user='root', password='', database='RecipeLab_database')

        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user and user[3] == password:
                session['username'] = user[1]
                session['user_id'] = user[0]  # Store user_id in session
                return redirect(url_for('dashboard'))
            else:
                return render_template("login.html", message="Invalid username or password !")

    return render_template('login.html')

# -------------- Dashboard ---------------

@app.route('/dashboard')
def dashboard():
    conn = MySQLdb.connect(host='localhost', user='root', password='', database='RecipeLab_database')
    cur = conn.cursor()
    cur.execute("SELECT p.id, p.content, p.user_id AS post_user_id, p.created_at AS post_created_at, c.comment_text, c.created_at AS comment_created_at, u.username AS comment_username, u_post.username AS post_username FROM posts p LEFT JOIN comments c ON p.id = c.post_id LEFT JOIN users u ON c.user_id = u.id LEFT JOIN users u_post ON p.user_id = u_post.id ORDER BY p.id DESC")
    posts = cur.fetchall()
    cur.close()
    conn.close()

    # Structure posts data to make it more usable in the template
    formatted_posts = {}
    for post in posts:
        post_id = post[0]
        if post_id not in formatted_posts:
            formatted_posts[post_id] = {
                'content': post[1],
                'user_id': post[2], 
                'created_at': post[3].strftime('%H:%M %d-%m-%Y'),
                'username_post': post[7],  # Use post_username obtained from the query
                'comments': []
            }
        if post[4]:  # Check if comment exists
            formatted_posts[post_id]['comments'].append({
                'comment_text': post[4],
                'comment_created_at': post[5].strftime('%H:%M %d-%m-%Y'),
                'username': post[6]  # Username of the commenter
            })

    return render_template("dashboard.html", username=session.get('username'), posts=formatted_posts)

# ------------------- logout ---------------

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

import datetime

# -------------------  create post ---------------

@app.route('/dashboard/create_post', methods=["POST"])
def create_post():
    if request.method == "POST":
        content = request.form["content"]
        user_id = session.get('user_id')

        # Get the current date and time in the required format
        created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = MySQLdb.connect(host='localhost', user='root', password='', database='RecipeLab_database')
        cur = conn.cursor()

        # Use parameterized query to insert the post with created_at
        cur.execute("INSERT INTO posts (content, user_id, created_at) VALUES (%s, %s, %s)", (content, user_id, created_at))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('dashboard'))  # Redirect to home page after creating the post

    return redirect(url_for('dashboard'))  # If request method is not POST, redirect to home page

# ------------------- create comment ---------------

@app.route('/dashboard/create_comment', methods=["POST"])
def create_comment():
    if request.method == "POST":
        post_id = request.form["post_id"]
        comment_text = request.form["comment_text"]
        user_id = session.get('user_id')

        conn = MySQLdb.connect(host='localhost', user='root', password='', database='RecipeLab_database')
        cur = conn.cursor()
        cur.execute("INSERT INTO comments (post_id, user_id, comment_text) VALUES (%s, %s, %s)", (post_id, user_id, comment_text))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('dashboard'))  # Redirect to dashboard after creating the comment

    return redirect(url_for('dashboard'))  # If request method is not POST, redirect to dashboard


# run the app
if __name__ == '__main__':
    app.run(debug=True)
