import sqlite3

DB_NAME = "diet.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- USERS ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        status INTEGER DEFAULT 1,
        email TEXT,
        age INTEGER
    )
    """)
        # --------- ADD NEW USER PROFILE COLUMNS SAFELY ---------
    # Add name column safely
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
    except:
        pass
    # Gender
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")
    except:
        pass

    # Height (in cm)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN height REAL")
    except:
        pass

    # Weight (in kg)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN weight REAL")
    except:
        pass

    # Phone number
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except:
        pass

    # Profile completion flag
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_completed INTEGER DEFAULT 0")
    except:
        pass

    # Account created date
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN joined_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except:
        pass

    # ---------------- CALORIE HISTORY ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calorie_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        calories INTEGER NOT NULL,
        log_date DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # ---------------- BMI HISTORY ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bmi_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        weight REAL NOT NULL,
        height REAL NOT NULL,
        bmi REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    try:
        cursor.execute("ALTER TABLE bmi_history ADD COLUMN category TEXT")
    except:
        pass
     
     # ---------------- HYDRATION------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_intake (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        intake_date DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # ---------------- HYDRATION HISTORY ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hydration_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        weight REAL NOT NULL,
        water_required REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # ---------------- DOCTORS ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        experience INTEGER
    )
    """)

    # ---------------- EXERCISES ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercises(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        bmi_min REAL,
        bmi_max REAL,
        image TEXT,
        instructions TEXT
    )
    """)

    # ---------------- CONTACT / FEEDBACK ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
    
    # ---------------- CREATE DEFAULT ADMIN ----------------
    from werkzeug.security import generate_password_hash

    cursor.execute("SELECT COUNT(*) FROM users WHERE username=?", ("Admin",))
    admin_exists = cursor.fetchone()[0]

    if admin_exists == 0:
        hashed_password = generate_password_hash("Admin@123")
        cursor.execute("""
            INSERT INTO users (username, password, status)
            VALUES (?, ?, 1)
        """, ("Admin", hashed_password))
    conn.commit()
    conn.close()
