from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

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

    db.commit()

init_db()

@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO users (username,password) VALUES (?,?)",
                   (request.form["username"], request.form["password"]))
        db.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                          (request.form["username"], request.form["password"])).fetchone()
        if user:
            session["user"] = request.form["username"]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        db.execute("""
        INSERT INTO workouts (user, workout, duration, calories, notes, date)
        VALUES (?,?,?,?,?,?)
        """, (
            session["user"],
            request.form["workout"],
            request.form["duration"],
            request.form["calories"],
            request.form["notes"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()

    workouts = db.execute(
        "SELECT * FROM workouts WHERE user=? ORDER BY date",
        (session["user"],)
    ).fetchall()

    steps = random.randint(3000,12000)

    return render_template("dashboard.html", workouts=workouts, steps=steps)

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM workouts WHERE id=?", (id,))
    db.commit()
    return redirect("/dashboard")

# EDIT
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    db = get_db()

    if request.method == "POST":
        db.execute("""
        UPDATE workouts SET workout=?, duration=?, calories=?, notes=? WHERE id=?
        """, (
            request.form["workout"],
            request.form["duration"],
            request.form["calories"],
            request.form["notes"],
            id
        ))
        db.commit()
        return redirect("/dashboard")

    workout = db.execute("SELECT * FROM workouts WHERE id=?", (id,)).fetchone()
    return render_template("edit.html", w=workout)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Render fix
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
