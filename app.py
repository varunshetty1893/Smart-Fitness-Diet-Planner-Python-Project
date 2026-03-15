import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import re
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection, init_db
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


app = Flask(__name__)
app.secret_key = "diet_secret_key"

UPLOAD_FOLDER = "static/exercise"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,password,status) VALUES(?,?,1)",
                (username, password)
            )
            conn.commit()
            flash("Registration Successful!", "success")
            return redirect(url_for("login"))

        except:
            flash("Username already exists!", "danger")

        finally:
            conn.close()

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):

            if user[3] == 0:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("login"))

            session["user_id"] = user[0]
            session["username"] = user[1]

            # If admin username
            if user[1] == "Admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        else:
            flash("Invalid Username or Password!", "danger")

    return render_template("login.html")

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form.get("username")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Password mismatch
        if new_password != confirm_password:
            return redirect(url_for("forgot_password", mismatch=1))

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Check if username exists
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        if not user:
            conn.close()
            return redirect(url_for("forgot_password", notfound=1))

        # Update password
        hashed_password = generate_password_hash(new_password)

        cur.execute("""
            UPDATE users SET password=? WHERE username=?
        """, (hashed_password, username))

        conn.commit()
        conn.close()

        # Redirect to login page with success message
        return redirect(url_for("login", reset=1))

    mismatch = request.args.get("mismatch")
    notfound = request.args.get("notfound")

    return render_template(
        "forgot_password.html",
        mismatch=mismatch,
        notfound=notfound
    )

    # ---------------- MANAGE USERS ----------------
@app.route("/admin/users")
def manage_users():

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    conn.close()

    return render_template("manage_users.html", users=users)

@app.route("/admin/activate/<int:user_id>")
def activate_user(user_id):

    if "username" not in session or session["username"].lower() != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manage_users"))


@app.route("/admin/deactivate/<int:user_id>")
def deactivate_user(user_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()

    if user and user[0] == "Admin":
        conn.close()
        return "<script>alert('Admin account cannot be modified');window.location='/admin/users';</script>"

    cur.execute("UPDATE users SET status=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manage_users"))


@app.route("/admin/delete/<int:user_id>")
def delete_user(user_id):

    if "username" not in session or session["username"].lower() != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manage_users"))

# ---------------- DASHBOARD ----------------
from datetime import datetime
import json

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # ---------------- Latest BMI ----------------
    cur.execute(
        "SELECT bmi FROM bmi_history WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (session["user_id"],)
    )
    row = cur.fetchone()
    bmi = row[0] if row else 0

    # ---------------- Latest Water ----------------
    cur.execute(
        "SELECT water_required FROM hydration_history WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (session["user_id"],)
    )
    row = cur.fetchone()
    water = row[0] if row else 0

    # ---------------- Count ----------------
    cur.execute("SELECT COUNT(*) FROM bmi_history WHERE user_id=?",
                (session["user_id"],))
    total_bmi = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM hydration_history WHERE user_id=?",
                (session["user_id"],))
    total_water = cur.fetchone()[0]

    # ---------------- BMI Trend (Last 7) ----------------
    cur.execute("""
        SELECT bmi, created_at
        FROM bmi_history
        WHERE user_id=?
        ORDER BY id ASC
        LIMIT 7
    """, (session["user_id"],))
    bmi_rows = cur.fetchall()

    bmi_labels = []
    bmi_values = []

    for row in bmi_rows:
        try:
            date_obj = datetime.strptime(row[1], "%d-%m-%Y %H:%M:%S")
            formatted_date = date_obj.strftime("%d %b")
        except:
            formatted_date = row[1]  # fallback if format mismatch

        bmi_labels.append(formatted_date)
        bmi_values.append(row[0])

    # ---------------- Water Trend (Last 7) ----------------
    cur.execute("""
        SELECT water_required, created_at
        FROM hydration_history
        WHERE user_id=?
        ORDER BY id ASC
        LIMIT 7
    """, (session["user_id"],))
    water_rows = cur.fetchall()

    water_labels = []
    water_values = []

    for row in water_rows:
        try:
            date_obj = datetime.strptime(row[1], "%d-%m-%Y %H:%M:%S")
            formatted_date = date_obj.strftime("%d %b")
        except:
            formatted_date = row[1]

        water_labels.append(formatted_date)
        water_values.append(row[0])

    conn.close()

    # ---------------- BMI Category ----------------
    if bmi == 0:
        bmi_category = "-"
        health_message = "Start tracking your health today."
    elif bmi < 18.5:
        bmi_category = "Underweight"
        health_message = "You are underweight. Improve your diet."
    elif bmi <= 24.9:
        bmi_category = "Normal"
        health_message = "Great! You are in healthy range."
    else:
        bmi_category = "Overweight"
        health_message = "Try exercise and proper diet."

    today_date = datetime.now().strftime("%d %B %Y")

    return render_template(
        "user_dashboard.html",
        username=session["username"],
        today_date=today_date,
        bmi=bmi,
        water=water,
        total_bmi=total_bmi,
        total_water=total_water,
        bmi_category=bmi_category,
        health_message=health_message,
        bmi_labels=json.dumps(bmi_labels),
        bmi_values=json.dumps(bmi_values),
        water_labels=json.dumps(water_labels),
        water_values=json.dumps(water_values)
    )
# ---------------- BMI HISTORY ----------------
@app.route("/bmi-history")
def bmi_history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT bmi, weight, height, category, created_at
        FROM bmi_history
        WHERE user_id = ?
        ORDER BY id ASC
    """, (session["user_id"],))

    records = cur.fetchall()
    conn.close()

    bmi_values = [row[0] for row in records]
    dates = [row[4] for row in records]

    latest_bmi = bmi_values[-1] if bmi_values else "-"
    highest_bmi = max(bmi_values) if bmi_values else "-"
    lowest_bmi = min(bmi_values) if bmi_values else "-"
    total_records = len(records)

    return render_template(
        "bmi_history.html",
        records=records,
        bmi_values=bmi_values,
        dates=dates,
        latest_bmi=latest_bmi,
        highest_bmi=highest_bmi,
        lowest_bmi=lowest_bmi,
        total_records=total_records
    )

# ---------------- BMI ----------------
from datetime import datetime
import random

@app.route("/bmi", methods=["GET", "POST"])
def bmi():

    if "user_id" not in session:
        return redirect(url_for("login"))

    result = None
    doctors = []

    if request.method == "POST":

        try:
            height = float(request.form["height"])
            weight = float(request.form["weight"])
        except:
            return render_template("bmi.html",
                                   result=None,
                                   doctors=[])

        height_m = height / 100
        bmi_value = round(weight / (height_m * height_m), 2)

        # BMI Category Logic
        if bmi_value < 18.5:
            category = "Underweight"
        elif bmi_value <= 24.9:
            category = "Normal"
        else:
            category = "Overweight"

        # Save in Database
        conn = get_connection()
        cur = conn.cursor()

        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        cur.execute("""
            INSERT INTO bmi_history (user_id, height, weight, bmi, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session["user_id"], height, weight, bmi_value, category, now))

        conn.commit()

        # Get 2 random doctors
        cur.execute("""
            SELECT * FROM doctors
            ORDER BY RANDOM()
            LIMIT 2
        """)

        doctors = cur.fetchall()

        conn.close()

        result = {
            "bmi": bmi_value,
            "category": category,
            "time": now
        }

    return render_template("bmi.html",
                           result=result,
                           doctors=doctors)


# ---------------- HYDRATION ----------------
from datetime import datetime

@app.route("/hydration", methods=["GET", "POST"])
def hydration():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    result = None

    # ---------------- NEW WEIGHT CALCULATION ----------------
    if request.method == "POST" and "weight" in request.form:

        weight = float(request.form["weight"])
        water_required = round(weight * 0.033, 2)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("""
            INSERT INTO hydration_history (user_id, weight, water_required, created_at)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], weight, water_required, now))

        conn.commit()

    # ---------------- ADD WATER INTAKE ----------------
    if request.method == "POST" and "add_amount" in request.form:

        amount = float(request.form["add_amount"])

        cur.execute("""
            INSERT INTO water_intake (user_id, amount)
            VALUES (?, ?)
        """, (session["user_id"], amount))

        conn.commit()

    # ---------------- FETCH LATEST HYDRATION RECORD ----------------
    cur.execute("""
        SELECT weight, water_required, created_at
        FROM hydration_history
        WHERE user_id=?
        ORDER BY id DESC LIMIT 1
    """, (session["user_id"],))

    row = cur.fetchone()

    if row:
        result = {
            "weight": row[0],
            "water": row[1],
            "time": row[2]
        }

    # ---------------- GET TODAY INTAKE ----------------
    cur.execute("""
        SELECT SUM(amount)
        FROM water_intake
        WHERE user_id=? AND intake_date = DATE('now')
    """, (session["user_id"],))

    row = cur.fetchone()
    today_intake = row[0] if row[0] else 0

    conn.close()

    return render_template(
        "hydration.html",
        result=result,
        today_intake=round(today_intake, 2)
    )

# ---------------- HYDRATION HISTORY ----------------
@app.route("/hydration_history")
def hydration_history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT weight, water_required, created_at
        FROM hydration_history
        WHERE user_id=?
        ORDER BY id ASC
    """, (session["user_id"],))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return render_template(
            "hydration_history.html",
            history=[],
            latest=0,
            highest=0,
            lowest=0,
            total=0,
            chart_labels=[],
            chart_values=[]
        )

    values = [r[1] for r in rows]
    
    # 🔥 Now use real dates instead of Record 1, Record 2
    labels = [r[2].split(" ")[0] for r in rows]

    latest = values[-1]
    highest = max(values)
    lowest = min(values)
    total = len(rows)

    return render_template(
        "hydration_history.html",
        history=rows,
        latest=latest,
        highest=highest,
        lowest=lowest,
        total=total,
        chart_labels=json.dumps(labels),
        chart_values=json.dumps(values)
    )

# ---------------- EXERCISE SUGGESTION ----------------
@app.route("/exercise-suggestions")
def exercise_suggestions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Get latest BMI of logged-in user
    cur.execute("""
        SELECT bmi FROM bmi_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (session["user_id"],))

    row = cur.fetchone()

    exercises = []
    bmi_value = None

    if row:
        bmi_value = row[0]

        # Fetch 5 exercises based on BMI range
        cur.execute("""
            SELECT * FROM exercises
            WHERE bmi_min <= ? AND bmi_max >= ?
            ORDER BY RANDOM()
            LIMIT 5
        """, (bmi_value, bmi_value))

        exercises = cur.fetchall()

    conn.close()

    return render_template(
        "exercise_suggestions.html",
        exercises=exercises,
        bmi_value=bmi_value
    )
# ---------------- USER PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        age = request.form.get("age")
        gender = request.form.get("gender")
        height = request.form.get("height")
        weight = request.form.get("weight")
        phone = request.form.get("phone")

        if not name or not age or not gender or not height or not weight:
            return redirect(url_for("profile", error=1))

        cur.execute("""
            UPDATE users
            SET name=?, email=?, age=?, gender=?, height=?, weight=?, phone=?, profile_completed=1
            WHERE id=?
        """, (name, email, age, gender, height, weight, phone, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for("profile", success=1))

    edit_mode = request.args.get("edit")
    success = request.args.get("success")
    error = request.args.get("error")

    cur.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
    user = cur.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        edit_mode=edit_mode,
        success=success,
        error=error
    )

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # TOTAL USERS
    cur.execute("SELECT COUNT(*) FROM users WHERE username != ?", ("Admin",))
    total_users = cur.fetchone()[0]

    # ACTIVE USERS
    cur.execute("""
    SELECT COUNT(*) FROM users
    WHERE status=1 AND username != ?
    """, ("Admin",))
    active_users = cur.fetchone()[0]

    # TOTAL DOCTORS
    cur.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cur.fetchone()[0]

    # TOTAL EXERCISES
    cur.execute("SELECT COUNT(*) FROM exercises")
    total_exercises = cur.fetchone()[0]

    # UNREAD FEEDBACK
    cur.execute("SELECT COUNT(*) FROM contact_messages WHERE is_read=0")
    unread_feedback = cur.fetchone()[0]

    # RECENT FEEDBACK
    cur.execute("""
        SELECT id, name, subject, created_at
        FROM contact_messages
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent_feedback = cur.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        active_users=active_users,
        total_doctors=total_doctors,
        total_exercises=total_exercises,
        unread_feedback=unread_feedback,
        recent_feedback=recent_feedback
    )

# ---------------- CONTACT ----------------
@app.route("/contact", methods=["GET","POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO contact_messages(name,email,subject,message)
            VALUES(?,?,?,?)
        """,(name,email,subject,message))

        conn.commit()
        conn.close()

        return redirect(url_for("home") + "#contact")

    return redirect(url_for("home") + "#contact")


# ---------------- USER CHANGE PASSWORD ----------------
@app.route("/user_change_password", methods=["GET", "POST"])
def user_change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "POST":

        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Fetch current stored password
        cur.execute("SELECT password FROM users WHERE id=?", (session["user_id"],))
        user = cur.fetchone()

        # Check current password
        if not check_password_hash(user["password"], current_password):
            conn.close()
            return redirect(url_for("user_change_password", error=1))

        # Check new password match
        if new_password != confirm_password:
            conn.close()
            return redirect(url_for("user_change_password", mismatch=1))

        # Optional: Minimum length validation
        if len(new_password) < 6:
            conn.close()
            return redirect(url_for("user_change_password", weak=1))

        # Update password
        hashed_password = generate_password_hash(new_password)

        cur.execute("""
            UPDATE users SET password=? WHERE id=?
        """, (hashed_password, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for("user_change_password", success=1))

    success = request.args.get("success")
    error = request.args.get("error")
    mismatch = request.args.get("mismatch")
    weak = request.args.get("weak")

    conn.close()

    return render_template(
        "user_change_password.html",
        success=success,
        error=error,
        mismatch=mismatch,
        weak=weak
    )


# ---------------- UPDATE PROFILE ----------------
@app.route("/update_profile", methods=["POST"])
def update_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    new_username = request.form["username"]

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("UPDATE users SET username=? WHERE id=?",
                    (new_username, session["user_id"]))
        conn.commit()

        session["username"] = new_username
        flash("Profile updated successfully!", "success")

    except:
        flash("Username already taken!", "danger")

    conn.close()

    return redirect(url_for("profile"))


# ------------------ MANAGE DOCTORS ------------------

@app.route("/admin/doctors")
def manage_doctors():

    if "username" not in session or session["username"].lower() != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM doctors ORDER BY id DESC")
    doctors = cur.fetchall()
    conn.close()

    return render_template("manage_doctors.html", doctors=doctors)


# ------------------ ADD DOCTOR ------------------
@app.route("/admin/add-doctor", methods=["POST"])
def add_doctor():

    if "username" not in session or session["username"].lower() != "admin":
        return redirect(url_for("login"))

    name = request.form["name"].strip()
    specialization = request.form["specialization"].strip()
    phone = request.form["phone"].strip()
    email = request.form["email"].strip()
    experience = request.form["experience"].strip()

    if not name.lower().startswith("dr"):
        name = "Dr. " + name

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO doctors(name, specialization, phone, email, experience)
        VALUES (?, ?, ?, ?, ?)
    """, (name, specialization, phone, email, int(experience)))

    conn.commit()
    conn.close()

    return redirect(url_for("manage_doctors"))

# ------------------ DELETE DOCTOR ------------------

@app.route("/admin/delete-doctor/<int:id>")
def delete_doctor(id):

    if "username" not in session or session["username"].lower() != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM doctors WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manage_doctors"))

# ---------------- MANAGE EXERCISES ----------------
@app.route("/admin/exercises")
def manage_exercises():

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exercises ORDER BY id DESC")
    exercises = cur.fetchall()
    conn.close()

    return render_template("manage_exercises.html", exercises=exercises)

@app.route("/admin/add-exercise", methods=["POST"])
def add_exercise():

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    name = request.form["name"]
    category = request.form["category"]
    bmi_min = request.form["bmi_min"]
    bmi_max = request.form["bmi_max"]
    instructions = request.form["instructions"]
    image = request.files["image"]

    # Save image
    filename = ""
    if image and image.filename != "":
        filename = secure_filename(image.filename)

        upload_folder = os.path.join("static", "exercise")
        os.makedirs(upload_folder, exist_ok=True)

        image.save(os.path.join(upload_folder, filename))

    # Insert into DB
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO exercises(name, category, bmi_min, bmi_max, image, instructions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, category, float(bmi_min), float(bmi_max), filename, instructions))

    conn.commit()
    conn.close()

    return redirect(url_for("manage_exercises"))
@app.route("/admin/delete-exercise/<int:id>")
def delete_exercise(id):

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM exercises WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manage_exercises"))

# ---------------- OVERALL ADMIN FEEDBACK ----------------
@app.route("/admin/feedback")
def admin_feedback():

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()

    per_page = 5
    offset = (page - 1) * per_page

    conn = get_connection()
    cur = conn.cursor()

    # ---------------- UNREAD COUNT ----------------
    cur.execute("SELECT COUNT(*) FROM contact_messages WHERE is_read = 0")
    unread_count = cur.fetchone()[0]

    # ---------------- SEARCH + DATA FETCH ----------------
    if search:
        search_term = f"%{search}%"

        # COUNT
        cur.execute("""
            SELECT COUNT(*) 
            FROM contact_messages
            WHERE LOWER(name) LIKE LOWER(?)
               OR LOWER(email) LIKE LOWER(?)
               OR LOWER(subject) LIKE LOWER(?)
        """, (search_term, search_term, search_term))

        total = cur.fetchone()[0]

        # FETCH DATA
        cur.execute("""
            SELECT id, name, email, subject, message,
                   is_read, created_at
            FROM contact_messages
            WHERE LOWER(name) LIKE LOWER(?)
               OR LOWER(email) LIKE LOWER(?)
               OR LOWER(subject) LIKE LOWER(?)
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (search_term, search_term, search_term, per_page, offset))

    else:
        # COUNT ALL
        cur.execute("SELECT COUNT(*) FROM contact_messages")
        total = cur.fetchone()[0]

        # FETCH ALL
        cur.execute("""
            SELECT id, name, email, subject, message,
                   is_read, created_at
            FROM contact_messages
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

    feedbacks = cur.fetchall()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "admin_feedback.html",
        feedbacks=feedbacks,
        page=page,
        total_pages=total_pages,
        search=search,
        unread_count=unread_count   # ✅ IMPORTANT
    )

@app.route("/admin/mark-read/<int:id>")
def mark_read(id):

    if "username" not in session or session["username"] != "Admin":
        return {"success": False}

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE contact_messages SET is_read=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return {"success": True}

# ---------------- REPLY FEEDBACK ----------------
@app.route("/admin/reply/<int:id>", methods=["GET", "POST"])
def reply_feedback(id):

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name,email,subject FROM contact_messages WHERE id=?", (id,))
    feedback = cur.fetchone()

    if not feedback:
        conn.close()
        return redirect(url_for("admin_feedback"))

    if request.method == "POST":

        reply_message = request.form["reply"]

        sender_email = "yourgmail@gmail.com"
        sender_password = "your_app_password"   # MUST BE APP PASSWORD

        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = feedback[1]
        msg["Subject"] = "Reply: " + feedback[2]

        msg.attach(MIMEText(reply_message, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()

            # Mark as read
            cur.execute("UPDATE contact_messages SET is_read=1 WHERE id=?", (id,))
            conn.commit()

        except Exception as e:
            print("Email Error:", e)

        conn.close()
        return redirect(url_for("admin_feedback"))

    conn.close()
    return render_template("reply.html", feedback=feedback, id=id)

@app.route("/admin/delete-feedback/<int:id>")
def delete_feedback(id):

    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM contact_messages WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_feedback"))

# ---------------- ADMIN PASSWORD CHANGE ----------------
from werkzeug.security import check_password_hash, generate_password_hash

@app.route("/admin/change-password", methods=["GET", "POST"])
def admin_change_password():

    # Ensure only logged-in admin can access
    if "username" not in session or session["username"] != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        conn = get_connection()
        cur = conn.cursor()

        # Get logged-in admin using session id
        cur.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
        user = cur.fetchone()

        if not user:
            conn.close()
            return "<script>alert('User not found');window.location='/login';</script>"

        # Check current password
        if not check_password_hash(user[2], current_password):
            conn.close()
            return "<script>alert('Current password is incorrect');window.history.back();</script>"

        # Confirm new passwords match
        if new_password != confirm_password:
            conn.close()
            return "<script>alert('New passwords do not match');window.history.back();</script>"

        # Hash new password
        hashed_password = generate_password_hash(new_password)

        # Update password
        cur.execute("UPDATE users SET password=? WHERE id=?",
                    (hashed_password, session["user_id"]))

        conn.commit()
        conn.close()

        return "<script>alert('Password updated successfully');window.location='/admin/change-password';</script>"

    return render_template("admin_change_password.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
