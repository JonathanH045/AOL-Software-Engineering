from flask import Flask, render_template, request, redirect, url_for, flash,jsonify,session
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'marlong'

# Initialize database (create table if not exists)
def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL,
                            is_admin INTEGER DEFAULT 0
                        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS forum_posts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            author TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS forum_replies (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            post_id INTEGER NOT NULL,
                            reply_text TEXT NOT NULL,
                            author_email TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (post_id) REFERENCES forum_posts(id)
                        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS educational_resources (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            description TEXT NOT NULL,
                            content TEXT NOT NULL,
                            author TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )''')
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_content_by_id(content_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM educational_resources WHERE id = ?", (content_id,))
    content = cursor.fetchone()
    conn.close()
    return content

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('database.db')
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        session['email'] = email
        session['is_admin'] = bool(user[3])  # user[3] is is_admin
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'})

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    data = request.get_json()
    email = data.get('email')
    password = generate_password_hash(data.get('password'))

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            is_admin = 1 if count == 0 else 0

            conn.execute("INSERT INTO users (email, password, is_admin) VALUES (?, ?, ?)", (email, password, is_admin))
            conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists.'})

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('home.html')
@app.route('/edu')
@login_required
def edu():
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        contents = conn.execute("SELECT * FROM educational_resources ORDER BY created_at DESC").fetchall()
    return render_template('edu.html', educational_contents=contents)

@app.route('/forum')
@login_required
def forum():
    with sqlite3.connect('database.db') as conn:
        posts = conn.execute("SELECT * FROM forum_posts ORDER BY created_at DESC").fetchall()
    return render_template('forum.html', posts=posts)
@app.route('/crforum', methods=['GET', 'POST'])
@login_required
def crforum():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['email']

        with sqlite3.connect('database.db') as conn:
            conn.execute("INSERT INTO forum_posts (title, content, author) VALUES (?, ?, ?)",
                         (title, content, author))
            conn.commit()

        return redirect(url_for('forum'))

    return render_template('crforum.html')

@app.route('/forum/<int:post_id>', methods=['GET', 'POST'])
def forum_detail(post_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    if request.method == 'POST':
        reply_text = request.form['reply']
        author = session.get('email') or 'Anonymous'
        conn.execute(
            "INSERT INTO forum_replies (post_id, reply_text, author_email) VALUES (?, ?, ?)",
            (post_id, reply_text, author)
        )
        conn.commit()

    post = conn.execute("SELECT * FROM forum_posts WHERE id = ?", (post_id,)).fetchone()
    replies = conn.execute("SELECT * FROM forum_replies WHERE post_id = ? ORDER BY created_at", (post_id,)).fetchall()
    conn.close()

    return render_template("forumreplies.html", post=post, replies=replies)
@app.route('/consult')
@login_required
def consult():
    return render_template('consult.html')

@app.route('/create_edu', methods=['GET', 'POST'])
@login_required
def create_edu():
    if not session.get('is_admin'):
        flash("Only admins can create educational content.", "danger")
        return redirect(url_for('edu'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        content = request.form['content']
        author = session['email']

        with sqlite3.connect('database.db') as conn:
            conn.execute('''INSERT INTO educational_resources (title, description, content, author)
                            VALUES (?, ?, ?, ?)''',
                         (title, description, content, author))
            conn.commit()

        return redirect(url_for('edu'))

    return render_template('create_edu.html')
@app.route('/edu/<int:content_id>')
@login_required
def view_edu(content_id):
    # Fetch content by ID and render a detail page
    content = get_content_by_id(content_id)  # Implement this function
    return render_template('edu_detail.html', content=content)
if __name__ == '__main__':
    app.run(debug=True)
