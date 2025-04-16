from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
import mysql.connector
import random
from db_config import get_db_connection
import re

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
            stored_hashed_password = result[0].encode('utf-8')

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

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        room_id = request.form.get("room_id")
        user_email = request.form.get("user_email")

        if not room_id or not user_email:
            flash("All fields are required!", "danger")
            return redirect(url_for("join"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_rooms WHERE room_id = %s", (room_id,))
        room = cursor.fetchone()
        cursor.close()
        conn.close()

        if not room:
            flash("Room ID not found. Please check again!", "danger")
            return redirect(url_for("join"))

        # ✅ Store email or name in session
        session["username"] = user_email  # Or get/display actual username if available

        flash("Successfully joined the game!", "success")
        return redirect(url_for("game_lobby", room_id=room_id))

    return render_template("join.html")


@app.route("/game_lobby/<room_id>")
def game_lobby(room_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM game_rooms WHERE room_id = %s", (room_id,))
    game = cursor.fetchone()
    cursor.close()
    conn.close()

    if not game:
        flash("Game room not found!", "danger")
        return redirect(url_for("home2"))

    return render_template("game_lobby.html", room_id=game["room_id"], game_type=game["game_type"], created_by=game["created_by"])


@app.route("/start_game/<room_id>", methods=["POST"])
def start_game(room_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE game_rooms SET status = 'started' WHERE room_id = %s", (room_id,))
    conn.commit()
    cursor.execute("SELECT game_type FROM game_rooms WHERE room_id = %s", (room_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        flash("Game room not found.", "danger")
        return redirect(url_for("home2"))

    game_type = result[0].strip().lower()

    if game_type == "mcq":
        return redirect(url_for("play_mcq", room_id=room_id))
    elif game_type == "paragraph":
        return redirect(url_for("play_paragraph", room_id=room_id))
    elif game_type == "picture":
        return redirect(url_for("play_picture", room_id=room_id))
    elif game_type == "fillblanks":
        return redirect(url_for("play_fillblanks", room_id=room_id))
    else:
        flash("Invalid game type.", "danger")
        return redirect(url_for("home2"))


@app.route("/play_mcq/<room_id>")
def play_mcq(room_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, option1, option2, option3, option4 FROM mcq_questions WHERE room_id = %s", (room_id,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()

    if not questions:
        flash("No questions found for this room.", "warning")
        return redirect(url_for("join"))

    return render_template("play_mcq.html", questions=questions, room_id=room_id)

@app.route("/play_paragraph/<room_id>")
def play_paragraph(room_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question FROM paragraph_questions WHERE room_id = %s", (room_id,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("play_paragraph.html", questions=questions, room_id=room_id)

@app.route("/play_picture/<room_id>")
def play_picture(room_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM picture_questions WHERE room_id = %s", (room_id,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("play_picture.html", room_id=room_id, questions=questions)



@app.route("/submit_answer/<int:question_id>", methods=["POST"])
def submit_answer(question_id):
    user_answer = request.form["answer"]
    room_id = request.form["room_id"]  # Get room_id from hidden input field

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT correct_answer FROM mcq_questions WHERE id = %s", (question_id,))
    correct_answer = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    if user_answer == correct_answer:
        flash("Correct answer! ✅", "success")
    else:
        flash("Wrong answer ❌. Try again!", "danger")

    if 'score' not in session:
        session['score'] = 0

    if user_answer == correct_answer:
        session['score'] += 1

    return redirect(url_for("play_mcq", room_id=room_id))

@app.route("/submit_paragraph_answer/<int:question_id>", methods=["POST"])
def submit_paragraph_answer(question_id):
    user_answer = request.form["answer"].strip().lower()
    room_id = request.form["room_id"]
    username = session.get("username", "Guest")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT correct_answer FROM paragraph_questions WHERE id = %s", (question_id,))
    question = cursor.fetchone()

    if not question:
        flash("Question not found.", "danger")
        return redirect(url_for("play_paragraph", room_id=room_id))

    correct_answer = question["correct_answer"].strip().lower()

    # Basic similarity check (exact match or partial match)
    if correct_answer in user_answer or user_answer in correct_answer:
        flash("✅ Correct answer!", "success")
        session["score"] = session.get("score", 0) + 1
    else:
        flash("❌ Incorrect answer!", "danger")

    cursor.close()
    conn.close()

    return redirect(url_for("play_paragraph", room_id=room_id))

@app.route("/submit_picture_answer/<int:question_id>", methods=["POST"])
def submit_picture_answer(question_id):
    answer = request.form["answer"].strip().lower()
    room_id = request.form["room_id"]
    username = session.get("username")
    
    if not username:
        flash("You must be logged in to play.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT correct_answer FROM picture_questions WHERE id = %s", (question_id,))
    correct = cursor.fetchone()
    
    if correct and answer == correct["correct_answer"].strip().lower():
        session["score"] = session.get("score", 0) + 1
    
    cursor.close()
    conn.close()

    return redirect(url_for("play_picture", room_id=room_id))


@app.route("/finish/<room_id>")
def finish_game(room_id):
    username = session.get("username")
    score = session.get("score", 0)

    if not username:
        flash("User not logged in!", "danger")
        return redirect(url_for("login"))  # Or your login route

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT game_type FROM game_rooms WHERE room_id = %s", (room_id,))
    game_info = cursor.fetchone()

    if not game_info:
        flash("Game room not found.", "danger")
        return redirect(url_for("home2"))

    game_type = game_info["game_type"].strip().lower()
    question_tables = {
        "mcq": "mcq_questions",
        "paragraph": "paragraph_questions",
        "picture": "picture_questions",
        "fillblanks": "fillblanks_questions"
    }

    table = question_tables.get(game_type)
    if not table:
        flash("Unsupported game type.", "danger")
        return redirect(url_for("home2"))

    cursor.execute(f"SELECT COUNT(*) AS total FROM {table} WHERE room_id = %s", (room_id,))
    total_questions = cursor.fetchone()["total"]

    if not username:
        flash("Session expired or username missing.", "danger")
        return redirect(url_for("join"))

    try:
        cursor.execute(
            "INSERT INTO players (username, room_id, game_type, score) VALUES (%s, %s, %s, %s)",
            (username, room_id, game_info["game_type"], score)
        )
        conn.commit()
        print("✅ Inserted player score:", username, score)
    except Exception as e:
        print("❌ Insert failed:", e)
        flash(f"Insert failed: {e}", "danger")

    cursor.close()
    conn.close()

    session.pop("score", None)

    return redirect(url_for("leaderboard", room_id=room_id))


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        created_by = request.form.get("created_by")
        game_type = request.form.get("game_type")

        if not created_by or not game_type:
            flash("All fields are required!", "danger")
            return redirect(url_for("create"))

        room_id = f"QM{random.randint(1000, 9999)}"
        session["room_id"] = room_id

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO game_rooms (room_id, created_by, game_type) VALUES (%s, %s, %s)",
            (room_id, created_by, game_type),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Game Room {room_id} Created!", "success")

        if game_type == "MCQ":
            return redirect(url_for("mcq", room_id=room_id))
        elif game_type == "Paragraph":
            return redirect(url_for("paragraph", room_id=room_id))
        elif game_type == "Picture Based":
            return redirect(url_for("picture", room_id=room_id))
        elif game_type == "Fill The Blanks":
            return redirect(url_for("fillblanks", room_id=room_id))
        else:
            flash("Invalid game type!", "danger")
            return redirect(url_for("create"))

    return render_template("create.html")


@app.route("/mcq/<room_id>", methods=["GET", "POST"])
def mcq(room_id):
    if request.method == "POST":
        action = request.form.get("action")
        question = request.form["question"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_answer = request.form["correct_answer"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mcq_questions (room_id, question, option1, option2, option3, option4, correct_answer) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (room_id, question, option1, option2, option3, option4, correct_answer)
        )
        conn.commit()
        cursor.close()
        conn.close()

        if action == "add":
            flash("MCQ added successfully! Add another question.", "success")
            return redirect(url_for("mcq", room_id=room_id))
        elif action == "finish":
            flash(f"Game Room {room_id} created successfully!", "success")
            return redirect(url_for("home2"))

    return render_template("mcq.html", room_id=room_id)


@app.route("/picture/<room_id>", methods=["GET", "POST"])
def picture(room_id):
    if request.method == "POST":
        question = request.form["question"]
        image_url = request.form["image_url"]
        correct_answer = request.form["correct_answer"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO picture_questions (room_id, question, image_url, correct_answer) VALUES (%s, %s, %s, %s)",
            (room_id, question, image_url, correct_answer)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Picture-based question added successfully!", "success")

    return render_template("picture.html", room_id=room_id)


@app.route("/paragraph/<room_id>", methods=["GET", "POST"])
def paragraph(room_id):
    if request.method == "POST":
        question = request.form["question"]
        correct_answer = request.form["correct_answer"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO paragraph_questions (room_id, question, correct_answer) VALUES (%s, %s, %s)",
            (room_id, question, correct_answer)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Paragraph question added successfully!", "success")

    return render_template("paragraph.html", room_id=room_id)


@app.route("/fillblanks", methods=["GET", "POST"])
def fillblanks(room_id):
    if request.method == "POST":
        question = request.form["question"]
        correct_answer = request.form["correct_answer"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fill_questions (room_id, question, correct_answer) VALUES (%s, %s, %s)",
            (room_id, question, correct_answer)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Fill in the blank question added successfully!", "success")

    return render_template("fill.html", room_id=room_id)


@app.route("/leaderboard/<room_id>")
def leaderboard(room_id):
    username = session.get("username")  # Get current user's name
    if not username:
        flash("User not logged in!", "danger")
        return redirect(url_for("login"))  # Or redirect to your join page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, score FROM players
        WHERE room_id = %s
        ORDER BY score DESC
    """, (room_id,))
    players = cursor.fetchall()

    cursor.close()
    conn.close()

    # Find the current player's rank
    current_rank = None
    for index, player in enumerate(players, start=1):
        if player["username"] == username:
            current_rank = index
            break

    return render_template("leaderboard.html",
                           players=players,
                           room_id=room_id,
                           current_player=username,
                           current_rank=current_rank)


# ✅ Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
