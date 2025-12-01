import os
"""
E-Thesis Portal: Bicol University Tabaco - Fisheries Department
Flask Application with Admin Panel and Public Access
Main Application File: main.py
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ================================
# USER CLASS
# ================================
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'])
    return None


# ================================
# DATABASE FUNCTIONS
# ================================
def get_db_connection():
    conn = sqlite3.connect('ethesis.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create theses table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            year INTEGER NOT NULL,
            adviser TEXT NOT NULL,
            abstract TEXT NOT NULL,
            keywords TEXT NOT NULL,
            pdf_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create default admin (username: admin, password: admin123)
    try:
        hashed_password = generate_password_hash('admin123')
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                     ('admin', hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Already exists

    conn.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ================================
# ROUTES
# ================================
@app.route('/')
def index():
    conn = get_db_connection()

    search_query = request.args.get('search', '')
    year_filter = request.args.get('year', '')

    query = 'SELECT * FROM theses WHERE 1=1'
    params = []

    if search_query:
        query += ' AND (title LIKE ? OR authors LIKE ? OR keywords LIKE ?)'
        like = f'%{search_query}%'
        params.extend([like, like, like])

    if year_filter:
        query += ' AND year = ?'
        params.append(year_filter)

    query += ' ORDER BY year DESC, title ASC'

    theses = conn.execute(query, params).fetchall()
    years = conn.execute('SELECT DISTINCT year FROM theses ORDER BY year DESC').fetchall()
    conn.close()

    return render_template('index.html', theses=theses, years=years,
                           search_query=search_query, year_filter=year_filter)


@app.route('/thesis/<int:thesis_id>')
def view_thesis(thesis_id):
    conn = get_db_connection()
    thesis = conn.execute('SELECT * FROM theses WHERE id = ?', (thesis_id,)).fetchone()
    conn.close()

    if thesis is None:
        abort(404)

    return render_template('view_thesis.html', thesis=thesis)


@app.route('/download/<int:thesis_id>')
def download_thesis(thesis_id):
    conn = get_db_connection()
    thesis = conn.execute('SELECT * FROM theses WHERE id = ?', (thesis_id,)).fetchone()
    conn.close()

    if thesis is None or not thesis['pdf_filename']:
        abort(404)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], thesis['pdf_filename'])

    if not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=True,
                     download_name=f"{thesis['title']}.pdf")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password', 'warning')
            return render_template('login.html')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                user_obj = User(user['id'], user['username'])
                login_user(user_obj)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    theses = conn.execute('SELECT * FROM theses ORDER BY year DESC, title ASC').fetchall()
    conn.close()
    return render_template('dashboard.html', theses=theses)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_thesis():
    if request.method == 'POST':
        title = request.form.get('title')
        authors = request.form.get('authors')
        year = request.form.get('year')
        adviser = request.form.get('adviser')
        abstract = request.form.get('abstract')
        keywords = request.form.get('keywords')

        pdf_filename = None
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                pdf_filename = filename

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO theses (title, authors, year, adviser, abstract, keywords, pdf_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, authors, year, adviser, abstract, keywords, pdf_filename))
        conn.commit()
        conn.close()

        flash('Thesis added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_thesis.html')


@app.route('/edit/<int:thesis_id>', methods=['GET', 'POST'])
@login_required
def edit_thesis(thesis_id):
    conn = get_db_connection()
    thesis = conn.execute('SELECT * FROM theses WHERE id = ?', (thesis_id,)).fetchone()

    if thesis is None:
        conn.close()
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title')
        authors = request.form.get('authors')
        year = request.form.get('year')
        adviser = request.form.get('adviser')
        abstract = request.form.get('abstract')
        keywords = request.form.get('keywords')

        pdf_filename = thesis['pdf_filename']
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename and allowed_file(file.filename):

                if pdf_filename:
                    old_file = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                pdf_filename = filename

        conn.execute('''
            UPDATE theses 
            SET title=?, authors=?, year=?, adviser=?, abstract=?, keywords=?, pdf_filename=?
            WHERE id=?
        ''', (title, authors, year, adviser, abstract, keywords, pdf_filename, thesis_id))
        conn.commit()
        conn.close()

        flash('Thesis updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit_thesis.html', thesis=thesis)


@app.route('/delete/<int:thesis_id>')
@login_required
def delete_thesis(thesis_id):
    conn = get_db_connection()
    thesis = conn.execute('SELECT * FROM theses WHERE id = ?', (thesis_id,)).fetchone()

    if thesis is None:
        conn.close()
        abort(404)

    if thesis['pdf_filename']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], thesis['pdf_filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

    conn.execute('DELETE FROM theses WHERE id = ?', (thesis_id,))
    conn.commit()
    conn.close()

    flash('Thesis deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


# ================================
# DEPLOYMENT ENTRY POINT
# ================================
if __name__ == '__main__':
    print("=" * 60)
    print("E-Thesis Portal - Bicol University Tabaco")
    print("Fisheries Department")
    print("=" * 60)

    init_db()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

