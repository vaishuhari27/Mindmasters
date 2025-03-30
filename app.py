from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from db_config import get_db_connection
import re
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SESSION_TYPE'] = 'filesystem'

bcrypt = Bcrypt(app)

# ✅ Email Validation Function
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email)

# ✅ Password Strength Validation
def is_valid_password(password):
    pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$"
    return re.match(pattern, password)

@app.route("/")
def home2():
    print("User email in session:", session.get('user_email'))
    return render_template('home2.html')

# ✅ Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template("signup.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered!", "warning")
            cursor.close()
            conn.close()
            return render_template("signup.html")

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            conn.commit()
            flash("Signup successful! Please log in.", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")

# ✅ Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT password FROM users WHERE email = %s"
        cursor.execute(query, (user_email,))
        result = cursor.fetchone()

        if result:
            stored_hashed_password = result[0]
            if bcrypt.check_password_hash(stored_hashed_password, password):
                session["user_email"] = user_email
                session["logged_in"] = True
                flash("Logged in successfully!", "success")
                return redirect(url_for("home2"))
            else:
                flash("Invalid email or password. Please try again.", "danger")
        else:
            flash("Email not found. Please sign up first.", "danger")

        cursor.close()
        conn.close()

    return render_template("login.html")

# ✅ Logout Route
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('home2'))

# ✅ Join Room Route
@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        room_id = request.form["room_id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE room_id = %s", (room_id,))
        room = cursor.fetchone()
        cursor.close()
        conn.close()

        if room:
            flash(f"Joined room: {room_id}", "success")
            return redirect(url_for("home2"))
        else:
            flash("Room does not exist. Please check the room name.", "danger")

    return render_template("join.html")

@app.route("/create", methods=["GET", "POST"])
def create():
    if "user_email" not in session:
        flash("You must log in to create a game.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        game_type = request.form.get("game_type")
        if not game_type:
            flash("Please select a game type.", "warning")
            return redirect(url_for("create"))
        return redirect(url_for(game_type))

    return render_template("create.html")

# ✅ Routes for Adding Questions
@app.route("/mcq", methods=["GET", "POST"])
def mcq():
    if request.method == "POST":
        question = request.form["question"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_answer = request.form["correct_answer"]

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO mcq_questions (question, option1, option2, option3, option4, correct_answer) VALUES (%s, %s, %s, %s, %s, %s)",
                           (question, option1, option2, option3, option4, correct_answer))
            conn.commit()
            flash("MCQ question added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Error adding question: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("mcq.html")

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
