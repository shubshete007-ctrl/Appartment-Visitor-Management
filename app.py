
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super-secret-key-for-demo"  # change in real projects
DB_NAME = "visitors.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Visitors table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            flat_no TEXT NOT NULL,
            purpose TEXT,
            vehicle_no TEXT,
            check_in TEXT NOT NULL,
            check_out TEXT
        )
    """)

    # Residents table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            flat_no TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    """)

    # Security logs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guard_name TEXT NOT NULL,
            shift_start TEXT NOT NULL,
            shift_end TEXT,
            notes TEXT
        )
    """)

    # Users table for login
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT
        )
    """)

    # Seed default admin user if none exists
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        default_username = "admin"
        default_password = "admin123"
        password_hash = generate_password_hash(default_password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (default_username, password_hash, "admin")
        )
        print(f"Created default user -> username: {default_username}, password: {default_password}")

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(view):
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html", page_title="Login")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "").strip()

        if not username or not new_password:
            flash("Username and new password are required", "error")
            return redirect(url_for("forgot_password"))

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            conn.close()
            flash("User not found", "error")
            return redirect(url_for("forgot_password"))

        password_hash = generate_password_hash(new_password)
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user["id"])
        )
        conn.commit()
        conn.close()

        flash("Password updated. Please log in with your new password.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html", page_title="Forgot Password")

@app.route("/")
@login_required
def dashboard():
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")

    daily_count = conn.execute(
        "SELECT COUNT(*) AS c FROM visitors WHERE date(check_in) = ?",
        (today,)
    ).fetchone()["c"]

    inside_count = conn.execute(
        "SELECT COUNT(*) AS c FROM visitors WHERE check_out IS NULL"
    ).fetchone()["c"]

    total_residents = conn.execute(
        "SELECT COUNT(*) AS c FROM residents"
    ).fetchone()["c"]

    recent = conn.execute(
        "SELECT name, flat_no, check_in FROM visitors ORDER BY check_in DESC LIMIT 5"
    ).fetchall()

    conn.close()
    apartment_name = "Skyline Heights Residency"
    hero_image_url = "https://images.pexels.com/photos/439391/pexels-photo-439391.jpeg"

    return render_template(
        "dashboard.html",
        daily_count=daily_count,
        inside_count=inside_count,
        total_residents=total_residents,
        recent=recent,
        apartment_name=apartment_name,
        hero_image_url=hero_image_url,
        page_title="Dashboard"
    )

@app.route("/visitors")
@login_required
def visitors_page():
    conn = get_db_connection()
    visitors = conn.execute(
        "SELECT * FROM visitors ORDER BY check_in DESC"
    ).fetchall()
    conn.close()
    return render_template("visitors.html", visitors=visitors, page_title="Visitors")

@app.route("/visitors/add", methods=["POST"])
@login_required
def add_visitor():
    data = request.form
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    flat_no = data.get("flat_no", "").strip()
    purpose = data.get("purpose", "").strip()
    vehicle_no = data.get("vehicle_no", "").strip()

    if not name or not flat_no:
        flash("Name and Flat No are required", "error")
        return redirect(url_for("visitors_page"))

    check_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO visitors (name, phone, flat_no, purpose, vehicle_no, check_in)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, phone, flat_no, purpose, vehicle_no, check_in)
    )
    conn.commit()
    conn.close()

    flash("Visitor added successfully", "success")
    return redirect(url_for("visitors_page"))

@app.route("/visitors/checkout/<int:visitor_id>", methods=["POST"])
@login_required
def checkout_visitor(visitor_id):
    check_out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    conn.execute(
        "UPDATE visitors SET check_out = ? WHERE id = ? AND check_out IS NULL",
        (check_out, visitor_id)
    )
    conn.commit()
    conn.close()
    flash("Visitor checked out", "success")
    return redirect(url_for("visitors_page"))

@app.route("/residents")
@login_required
def residents():
    conn = get_db_connection()
    residents = conn.execute(
        "SELECT * FROM residents ORDER BY flat_no ASC"
    ).fetchall()
    conn.close()
    return render_template("residents.html", residents=residents, page_title="Resident List")

@app.route("/residents/add", methods=["POST"])
@login_required
def add_resident():
    data = request.form
    name = data.get("name", "").strip()
    flat_no = data.get("flat_no", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()

    if not name or not flat_no:
        flash("Name and Flat No are required", "error")
        return redirect(url_for("residents"))

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO residents (name, flat_no, phone, email)
        VALUES (?, ?, ?, ?)
        """,
        (name, flat_no, phone, email)
    )
    conn.commit()
    conn.close()

    flash("Resident added successfully", "success")
    return redirect(url_for("residents"))

@app.route("/security-logs")
@login_required
def security_logs():
    conn = get_db_connection()
    logs = conn.execute(
        "SELECT * FROM security_logs ORDER BY shift_start DESC"
    ).fetchall()
    conn.close()
    return render_template("security_logs.html", logs=logs, page_title="Security Logs")

@app.route("/security-logs/add", methods=["POST"])
@login_required
def add_security_log():
    data = request.form
    guard_name = data.get("guard_name", "").strip()
    notes = data.get("notes", "").strip()

    if not guard_name:
        flash("Guard name is required", "error")
        return redirect(url_for("security_logs"))

    shift_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO security_logs (guard_name, shift_start, notes)
        VALUES (?, ?, ?)
        """,
        (guard_name, shift_start, notes)
    )
    conn.commit()
    conn.close()

    flash("Guard shift started", "success")
    return redirect(url_for("security_logs"))

@app.route("/security-logs/end/<int:log_id>", methods=["POST"])
@login_required
def end_security_shift(log_id):
    shift_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    conn.execute(
        "UPDATE security_logs SET shift_end = ? WHERE id = ? AND shift_end IS NULL",
        (shift_end, log_id)
    )
    conn.commit()
    conn.close()
    flash("Guard shift ended", "success")
    return redirect(url_for("security_logs"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
