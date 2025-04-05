import sqlite3
from flask import Flask, g

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Optional: return rows as dict-like objects
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql') as f:
            db.executescript(f.read())

@app.route('/add')
def add_user():
    db = get_db()
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Alice", "alice@example.com"))
    db.commit()
    return "User added!"

@app.route('/')
def home():
    return "Hello, world!"

if __name__ == '__main__':
    app.run(debug=True)
