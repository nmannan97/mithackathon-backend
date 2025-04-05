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
                description TEXT NOT NULL CHECK(description <> ''),
                funding TEXT NOT NULL,
                wallet TEXT NOT NULL CHECK(wallet <> ''),
                role TEXT NOT NULL CHECK(role IN ('startup', 'investor'))
            )
        ''')
        db.commit()

with app.app_context():
    init_db()

@app.route('/', methods=['POST'])
def add_startup():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    funding = data.get('funding', '').strip()
    wallet = data.get('wallet', '').strip()
    role = data.get('role', '').strip().lower()

    if not all([name, description, wallet, role]):
        return jsonify({'error': 'These fields (name, description, wallet, role) are required.'}), 400

    if role not in ['startup', 'investor']:
        return jsonify({'error': 'Role must be either "startup" or "investor".'}), 400

    db = get_db()
    db.execute(
        'INSERT INTO startups (name, description, funding, wallet, role) VALUES (?, ?, ?, ?, ?)',
        (name, description, funding, wallet, role)
    )
    db.commit()

    return jsonify({'message': f'{role.capitalize()} "{name}" added successfully!'})

@app.route('/startups', methods=['GET'])
def get_startups():
    db = get_db()
    cursor = db.execute('SELECT id, name, description, funding, wallet, role FROM startups')
    rows = cursor.fetchall()
    startups = [dict(row) for row in rows]
    return jsonify(startups)

if __name__ == '__main__':
    app.run(debug=True)
