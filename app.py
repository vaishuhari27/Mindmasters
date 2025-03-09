from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from db_config import get_db_connection
import mysql.connector

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "your_secret_key"

db = mysql.connector.connect(
    host="localhost",
    user="vaishu",
    password="1999",
    database="mindmasters",
    charset="utf8mb4",
    collation="utf8mb4_general_ci"
)
cursor = db.cursor()
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[0], password):
            session["user"] = email
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route("/create-room", methods=["GET", "POST"])
def create_room():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        room_name = request.form["room_name"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rooms (room_name, created_by) VALUES (%s, %s)", (room_name, session["user"]))
        conn.commit()
        conn.close()

        return redirect(url_for("home"))
    return render_template("create_room.html")

if __name__ == "__main__":
    app.run(debug=True)


