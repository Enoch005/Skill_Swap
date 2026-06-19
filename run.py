from flask import Flask, render_template, request, redirect, session, flash
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

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # User Info
    cursor.execute(
        "SELECT full_name, email FROM users WHERE user_id=%s",
        (session['user_id'],)
    )

    user = cursor.fetchone()

    # Skills I Can Teach
    cursor.execute("""
        SELECT s.skill_name
        FROM user_skills us
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        AND us.skill_type = 'teach'
    """, (session['user_id'],))

    teach_skills = cursor.fetchall()

    # Skills I Want To Learn
    cursor.execute("""
        SELECT s.skill_name
        FROM user_skills us
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        AND us.skill_type = 'learn'
    """, (session['user_id'],))

    learn_skills = cursor.fetchall()

    # Get all skills for dropdown
    cursor.execute(
        "SELECT * FROM skills ORDER BY skill_name"
    )

    all_skills = cursor.fetchall()
    
    # Incoming Requests
    cursor.execute("""
    SELECT
    requests.request_id,
    users.full_name,
    skills.skill_name,
    requests.status
    FROM requests
    JOIN users
        ON requests.learner_id = users.user_id
    JOIN skills
        ON requests.skill_id = skills.skill_id
    WHERE requests.teacher_id = %s
""", (session['user_id'],))

    requests = cursor.fetchall()
    total_teach = len(teach_skills)
    total_learn = len(learn_skills)
    total_requests = len(requests)
    
    # My Connections
    cursor.execute("""
    SELECT
        users.full_name,
        users.email,
        skills.skill_name
    FROM connections
    JOIN users
        ON connections.teacher_id = users.user_id
    JOIN skills
        ON connections.skill_id = skills.skill_id
    WHERE connections.learner_id = %s
""", (session['user_id'],))

    connections = cursor.fetchall()
    
    total_connections = len(connections)
    
    cursor.close()
    connection.close()

    return render_template(
    'dashboard.html',
    user=user,
    teach_skills=teach_skills,
    learn_skills=learn_skills,
    all_skills=all_skills,
    requests=requests,
    connections=connections,
    total_teach=total_teach,
    total_learn=total_learn,
    total_requests=total_requests,
    total_connections=total_connections
)
    
@app.route('/find-teachers', methods=['POST'])
def find_teachers():

    skill_id = request.form['skill_id']

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        users.user_id,
        users.full_name,
        users.email,
        skills.skill_id,
        skills.skill_name
    FROM user_skills
    JOIN users
        ON user_skills.user_id = users.user_id
    JOIN skills
        ON user_skills.skill_id = skills.skill_id
    WHERE user_skills.skill_id = %s
    AND user_skills.skill_type = 'teach'
""", (skill_id,))

    teachers = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template(
        'teachers.html',
        teachers=teachers
    )
    
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # User Info
    cursor.execute(
        "SELECT * FROM users WHERE user_id=%s",
        (session['user_id'],)
    )

    user = cursor.fetchone()

    # Teaching Skills
    cursor.execute("""
        SELECT s.skill_name
        FROM user_skills us
        JOIN skills s
        ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        AND us.skill_type='teach'
    """, (session['user_id'],))

    teach_skills = cursor.fetchall()

    # Learning Skills
    cursor.execute("""
        SELECT s.skill_name
        FROM user_skills us
        JOIN skills s
        ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        AND us.skill_type='learn'
    """, (session['user_id'],))

    learn_skills = cursor.fetchall()

    # Connections Count
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM connections
        WHERE learner_id=%s
        OR teacher_id=%s
    """, (session['user_id'], session['user_id']))

    connection_count = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        'profile.html',
        user=user,
        teach_skills=teach_skills,
        learn_skills=learn_skills,
        connection_count=connection_count
    )

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

@app.route('/create-skill', methods=['POST'])
def create_skill():

    skill_name = request.form['skill_name']

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO skills(skill_name)
            VALUES(%s)
            """,
            (skill_name,)
        )

        connection.commit()

    except:
        pass

    cursor.close()
    connection.close()

    return redirect('/dashboard')

@app.route('/add-skill', methods=['POST'])
def add_skill():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    skill_id = request.form['skill_id']
    skill_type = request.form['skill_type']

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check duplicate
    cursor.execute(
        """
        SELECT *
        FROM user_skills
        WHERE user_id=%s
        AND skill_id=%s
        AND skill_type=%s
        """,
        (user_id, skill_id, skill_type)
    )

    existing_skill = cursor.fetchone()

    if existing_skill:
        cursor.close()
        connection.close()
        return redirect('/dashboard')

    # Insert new skill
    cursor.execute(
        """
        INSERT INTO user_skills
        (user_id, skill_id, skill_type)
        VALUES (%s, %s, %s)
        """,
        (user_id, skill_id, skill_type)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect('/dashboard')

@app.route('/send-request', methods=['POST'])
def send_request():

    if 'user_id' not in session:
        return redirect('/login')

    learner_id = session['user_id']
    teacher_id = request.form['teacher_id']
    skill_id = request.form['skill_id']
    
    if learner_id == int(teacher_id):
       flash("You cannot send a request to yourself!", "error")
       return redirect('/dashboard')

    # Create connection FIRST
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check duplicate request
    cursor.execute(
        """
        SELECT * FROM requests
        WHERE learner_id=%s
        AND teacher_id=%s
        AND skill_id=%s
        """,
        (learner_id, teacher_id, skill_id)
    )

    existing_request = cursor.fetchone()

    if existing_request:
        cursor.close()
        connection.close()
        flash("Request already sent!", "error")
        return redirect('/dashboard')

    # Insert new request
    cursor.execute(
        """
        INSERT INTO requests
        (learner_id, teacher_id, skill_id)
        VALUES (%s, %s, %s)
        """,
        (learner_id, teacher_id, skill_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash("Request sent successfully!", "success")
    return redirect('/dashboard')

@app.route('/accept-request', methods=['POST'])
def accept_request():

    request_id = request.form['request_id']

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get request details
    cursor.execute(
        """
        SELECT *
        FROM requests
        WHERE request_id=%s
        """,
        (request_id,)
    )

    request_data = cursor.fetchone()

    # Update request status
    cursor.execute(
        """
        UPDATE requests
        SET status='accepted'
        WHERE request_id=%s
        """,
        (request_id,)
    )

    # Create connection
    cursor.execute(
        """
        INSERT INTO connections
        (learner_id, teacher_id, skill_id)
        VALUES (%s, %s, %s)
        """,
        (
            request_data['learner_id'],
            request_data['teacher_id'],
            request_data['skill_id']
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)