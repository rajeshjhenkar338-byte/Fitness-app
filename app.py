from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

# Create tables if not exist
def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY,
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
        id INTEGER PRIMARY KEY,
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

    # Add workout
    if request.method == "POST":
        workout = request.form["workout"]
        duration = request.form["duration"]
        calories = request.form["calories"]
        notes = request.form["notes"]
        date = datetime.now()

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

    # Simulated steps
    steps = random.randint(2000, 10000)

    return render_template("dashboard.html", workouts=workouts, steps=steps, goals=goals)

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

app.run(debug=True)
