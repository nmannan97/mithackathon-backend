import sqlite3
from flask import Flask, g, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

DATABASE = 'mydatabase.sqlite3'
DATABASE_COIN = 'mydatabase_coins.sqlite3'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_coin_db():
    if 'coin_db' not in g:
        g.coin_db = sqlite3.connect(DATABASE_COIN)
        g.coin_db.row_factory = sqlite3.Row
    return g.coin_db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    coin_db = g.pop('coin_db', None)

    if db is not None:
        db.close()
    if coin_db is not None:
        coin_db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS startups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL CHECK(description <> ''),
                funding TEXT NOT NULL,
                wallet TEXT NOT NULL CHECK(wallet <> ''),
                role TEXT NOT NULL CHECK(role IN ('startup', 'investor'))
            )
        ''')
        db.commit()

def init_db_coins():
    with app.app_context():
        db = get_coin_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0)
            )
        ''')
        db.commit()

with app.app_context():
    init_db()
    init_db_coins()

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

@app.route('/coins', methods=['POST'])
def add_coin():
    data = request.get_json()
    name = data.get('name', '').strip()
    amount = data.get('amount')

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if amount is None or not isinstance(amount, (int, float)):
        return jsonify({'error': 'Amount must be a number'}), 400

    db = get_coin_db()

    # Check if coin with this name exists
    cursor = db.execute('SELECT amount FROM coins WHERE name = ?', (name,))
    existing = cursor.fetchone()
    old_amount = existing['amount'] if existing else 0

    # Get current total
    total_cursor = db.execute('SELECT SUM(amount) as total FROM coins')
    total_row = total_cursor.fetchone()
    current_total = total_row['total'] or 0

    # New total if we update this entry
    new_total = current_total - old_amount + amount

    if new_total > 100:
        return jsonify({'error': 'Coin amount exceeds 100'}), 400

    if existing:
        db.execute('UPDATE coins SET amount = ? WHERE name = ?', (amount, name))
    else:
        db.execute('INSERT INTO coins (name, amount) VALUES (?, ?)', (name, amount))
    db.commit()

    return jsonify({'message': f'✅ person "{name}" with amount {amount} added or updated.'})

@app.route('/coins', methods=['GET'])
def get_coins():
    db = get_coin_db()
    cursor = db.execute('SELECT id, name, amount FROM coins')
    rows = cursor.fetchall()
    coins = [dict(row) for row in rows]
    return jsonify(coins)

if __name__ == '__main__':
    app.run(debug=True)
