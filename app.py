from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

# Create tables
def init_db():
    db = get_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        workout TEXT,
        duration INTEGER,
        calories INTEGER,
        notes TEXT,
        date TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        goal TEXT
    )
    """)

    db.commit()

init_db()

@app.route("/")
def home():
    return redirect("/login")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        db = get_db()
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, password))
        db.commit()

        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        db = get_db()
        result = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (user, password)
        ).fetchone()

        if result:
            session["user"] = user
            return redirect("/dashboard")

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        workout = request.form["workout"]
        duration = request.form["duration"]
        calories = request.form["calories"]
        notes = request.form["notes"]
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.execute("""
        INSERT INTO workouts (user, workout, duration, calories, notes, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (session["user"], workout, duration, calories, notes, date))
        db.commit()

    workouts = db.execute(
        "SELECT * FROM workouts WHERE user=?",
        (session["user"],)
    ).fetchall()

    goals = db.execute(
        "SELECT * FROM goals WHERE user=?",
        (session["user"],)
    ).fetchall()

    steps = random.randint(2000, 10000)

    return render_template("dashboard.html", workouts=workouts, goals=goals, steps=steps)

# ADD GOAL
@app.route("/add_goal", methods=["POST"])
def add_goal():
    if "user" not in session:
        return redirect("/login")

    goal = request.form["goal"]

    db = get_db()
    db.execute("INSERT INTO goals (user, goal) VALUES (?, ?)", (session["user"], goal))
    db.commit()

    return redirect("/dashboard")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# IMPORTANT FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
