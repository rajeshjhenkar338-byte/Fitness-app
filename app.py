from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os
import random
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# DB connection
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
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
    db.commit()

init_db()

@app.route("/")
def home():
    return redirect("/login")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Fill all fields"

        db = get_db()
        db.execute("INSERT INTO users (username,password) VALUES (?,?)",
                   (username, generate_password_hash(password)))
        db.commit()

        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        workout = request.form.get("workout")
        duration = request.form.get("duration") or 0
        calories = request.form.get("calories") or 0
        notes = request.form.get("notes")

        db.execute("""
        INSERT INTO workouts (user, workout, duration, calories, notes, date)
        VALUES (?,?,?,?,?,?)
        """, (
            session["user"],
            workout,
            int(duration),
            int(calories),
            notes,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        db.commit()

    workouts = db.execute("SELECT * FROM workouts WHERE user=?", (session["user"],)).fetchall()

    steps = random.randint(3000,12000)

    return render_template("dashboard.html", workouts=workouts, steps=steps)

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM workouts WHERE id=?", (id,))
    db.commit()
    return redirect("/dashboard")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
