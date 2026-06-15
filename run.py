from flask import Flask, render_template, request, redirect, session
from app.config.db_config import get_db_connection

app = Flask(
    __name__,
    template_folder="templets",
    static_folder="app/static"
)

app.secret_key = "skillswap_secret_key"

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']

            return redirect('/dashboard')

        return "Invalid Email or Password"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template('dashboard.html')

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return "Email already exists!"

        cursor.execute(
            """
            INSERT INTO users(full_name, email, password)
            VALUES(%s, %s, %s)
            """,
            (full_name, email, password)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return "Registration Successful!"

    return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)