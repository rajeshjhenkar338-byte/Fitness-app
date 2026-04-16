from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
from datetime import datetime
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row   # IMPORTANT FIX
    return conn

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

# AI Suggestion
def get_suggestion(workouts):
    if not workouts:
        return "Start your fitness journey 💪"

    calories = [w["calories"] for w in workouts if w["calories"]]

    if not calories:
        return "Add workouts to get suggestions"

    avg = sum(calories) / len(calories)

    if avg < 200:
        return "Increase workout intensity 🔥"
    elif avg < 500:
        return "Good consistency 👍"
    else:
        return "Excellent performance 💯"

@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO users VALUES (NULL, ?, ?)",
                   (request.form["username"],
                    generate_password_hash(request.form["password"])))
        db.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?",
                          (request.form["username"],)).fetchone()

        if user and check_password_hash(user["password"], request.form["password"]):
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
            request.form.get("workout"),
            int(request.form.get("duration") or 0),
            int(request.form.get("calories") or 0),
            request.form.get("notes"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()

    workouts = db.execute(
        "SELECT * FROM workouts WHERE user=? ORDER BY date",
        (session["user"],)
    ).fetchall()

    steps = random.randint(3000,12000)
    suggestion = get_suggestion(workouts)

    return render_template("dashboard.html",
                           workouts=workouts,
                           steps=steps,
                           suggestion=suggestion)

@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM workouts WHERE id=?", (id,))
    db.commit()
    return redirect("/dashboard")

@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    db = get_db()

    if request.method == "POST":
        db.execute("""
        UPDATE workouts SET workout=?, duration=?, calories=?, notes=? WHERE id=?
        """, (
            request.form.get("workout"),
            int(request.form.get("duration") or 0),
            int(request.form.get("calories") or 0),
            request.form.get("notes"),
            id
        ))
        db.commit()
        return redirect("/dashboard")

    workout = db.execute("SELECT * FROM workouts WHERE id=?", (id,)).fetchone()
    return render_template("edit.html", w=workout)

@app.route("/download")
def download():
    db = get_db()
    workouts = db.execute(
        "SELECT workout, duration, calories, date FROM workouts WHERE user=?",
        (session["user"],)
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Workout","Duration","Calories","Date"])

    for w in workouts:
        writer.writerow([w["workout"], w["duration"], w["calories"], w["date"]])

    return Response(output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=report.csv"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
