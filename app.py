import sqlite3
from flask import Flask, g, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

DATABASE = 'mydatabase.sqlite3'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS startups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                funding TEXT
            )
        ''')
        db.commit()

with app.app_context():
    init_db()

# Replace "/" route to accept POST and add startup
@app.route('/', methods=['POST'])
def add_startup():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    funding = data.get('funding')

    db = get_db()
    db.execute(
        'INSERT INTO startups (name, description, funding) VALUES (?, ?, ?)',
        (name, description, funding)
    )
    db.commit()

    return jsonify({'message': f'Startup "{name}" added successfully!'})

@app.route('/startups', methods=['GET'])
def get_startups():
    db = get_db()
    cursor = db.execute('SELECT id, name, description, funding FROM startups')
    rows = cursor.fetchall()

    # Convert rows to list of dicts
    startups = [dict(row) for row in rows]
    return jsonify(startups)

if __name__ == '__main__':
    app.run(debug=True)
