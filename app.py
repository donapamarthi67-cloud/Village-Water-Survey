from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import sqlite3, os, uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "water_survey.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS households (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_head TEXT NOT NULL,
        mobile TEXT NOT NULL,
        village TEXT NOT NULL,
        ward TEXT NOT NULL,
        house_number TEXT,
        family_members INTEGER NOT NULL,
        male_members INTEGER,
        female_members INTEGER,
        children INTEGER,
        senior_citizens INTEGER,
        occupation TEXT,
        education TEXT,
        income_range TEXT,
        house_type TEXT,
        electricity TEXT,
        toilet TEXT,
        livelihood TEXT,
        water_source TEXT,
        water_availability TEXT,
        hours_per_day INTEGER,
        days_per_week INTEGER,
        distance TEXT,
        queue TEXT,
        purchases_water TEXT,
        water_clear TEXT,
        bad_smell TEXT,
        unusual_taste TEXT,
        contamination TEXT,
        water_illness TEXT,
        filtration TEXT,
        purifier TEXT,
        problems TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        ward TEXT NOT NULL,
        location TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        duration TEXT,
        households_affected INTEGER,
        photo TEXT,
        latitude REAL,
        longitude REAL,
        contact_method TEXT,
        status TEXT DEFAULT 'Submitted',
        authority_remarks TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS water_facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        ward TEXT NOT NULL,
        status TEXT NOT NULL,
        maintenance_date TEXT,
        households_served INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title_en TEXT NOT NULL,
        title_te TEXT NOT NULL,
        description_en TEXT NOT NULL,
        description_te TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM water_facilities").fetchone()[0] == 0:
        conn.executemany("""INSERT INTO water_facilities
            (name,type,location,ward,status,maintenance_date,households_served)
            VALUES (?,?,?,?,?,?,?)""", [
            ("Main Overhead Tank", "Water Tank", "Village Main Road", "1", "Working", "2026-07-15", 240),
            ("East Borewell", "Borewell", "East Street", "2", "Needs Maintenance", "2026-06-20", 95),
            ("Community Hand Pump", "Hand Pump", "School Road", "3", "Working", "2026-07-30", 70),
            ("Public Tap Point", "Public Tap", "Market Area", "4", "Not Working", "2026-05-18", 55),
        ])
    if conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0] == 0:
        conn.executemany("""INSERT INTO announcements
            (title_en,title_te,description_en,description_te) VALUES (?,?,?,?)""", [
            ("Scheduled Tank Cleaning", "నీటి ట్యాంక్ శుభ్రపరిచే కార్యక్రమం",
             "The main overhead tank will be cleaned on Sunday. Water supply may be interrupted.",
             "ప్రధాన నీటి ట్యాంక్‌ను ఆదివారం శుభ్రం చేస్తారు. నీటి సరఫరాలో తాత్కాలిక అంతరాయం ఉండవచ్చు."),
            ("Pipeline Repair", "పైప్‌లైన్ మరమ్మత్తు",
             "Pipeline repair work is planned near the market area.",
             "మార్కెట్ ప్రాంతంలో పైప్‌లైన్ మరమ్మత్తు పనులు జరుగనున్నాయి.")
        ])
    conn.commit()
    conn.close()

@app.context_processor
def inject_globals():
    return {"year": datetime.now().year}

@app.route("/")
def home():
    conn = db()
    facilities = conn.execute("SELECT * FROM water_facilities ORDER BY id LIMIT 4").fetchall()
    announcements = conn.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 3").fetchall()
    stats = {
        "households": conn.execute("SELECT COUNT(*) FROM households").fetchone()[0],
        "complaints": conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],
        "resolved": conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0],
        "facilities": conn.execute("SELECT COUNT(*) FROM water_facilities").fetchone()[0]
    }
    conn.close()
    return render_template("index.html", facilities=facilities, announcements=announcements, stats=stats)

@app.route("/survey", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        required = ["household_head","mobile","village","ward","family_members"]
        if any(not request.form.get(k, "").strip() for k in required):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("survey"))
        data = request.form
        conn = db()
        conn.execute("""INSERT INTO households (
            household_head,mobile,village,ward,house_number,family_members,male_members,
            female_members,children,senior_citizens,occupation,education,income_range,
            house_type,electricity,toilet,livelihood,water_source,water_availability,
            hours_per_day,days_per_week,distance,queue,purchases_water,water_clear,
            bad_smell,unusual_taste,contamination,water_illness,filtration,purifier,problems
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            data.get("household_head"),data.get("mobile"),data.get("village"),data.get("ward"),
            data.get("house_number"),data.get("family_members"),data.get("male_members"),
            data.get("female_members"),data.get("children"),data.get("senior_citizens"),
            data.get("occupation"),data.get("education"),data.get("income_range"),
            data.get("house_type"),data.get("electricity"),data.get("toilet"),
            data.get("livelihood"),data.get("water_source"),data.get("water_availability"),
            data.get("hours_per_day"),data.get("days_per_week"),data.get("distance"),
            data.get("queue"),data.get("purchases_water"),data.get("water_clear"),
            data.get("bad_smell"),data.get("unusual_taste"),data.get("contamination"),
            data.get("water_illness"),data.get("filtration"),data.get("purifier"),
            ", ".join(data.getlist("problems"))
        ))
        conn.commit()
        conn.close()
        return render_template("success.html", title_en="Survey Submitted", title_te="సర్వే సమర్పించబడింది",
                               message_en="Thank you. Your survey response has been recorded.",
                               message_te="ధన్యవాదాలు. మీ సర్వే వివరాలు విజయవంతంగా నమోదు చేయబడ్డాయి.")
    return render_template("survey.html")

@app.route("/complaint", methods=["GET", "POST"])
def complaint():
    if request.method == "POST":
        data = request.form
        if not all(data.get(k, "").strip() for k in ["name","mobile","ward","location","category","description"]):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("complaint"))

        photo_name = ""
        photo = request.files.get("photo")
        if photo and photo.filename:
            ext = photo.filename.rsplit(".", 1)[-1].lower() if "." in photo.filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                flash("Only JPG, JPEG and PNG files are allowed.", "danger")
                return redirect(url_for("complaint"))
            photo_name = f"{uuid.uuid4().hex}.{ext}"
            photo.save(os.path.join(UPLOAD_DIR, secure_filename(photo_name)))

        conn = db()
        complaint_no = f"WTR-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        conn.execute("""INSERT INTO complaints
            (complaint_number,name,mobile,ward,location,category,description,duration,
             households_affected,photo,latitude,longitude,contact_method)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            complaint_no,data["name"],data["mobile"],data["ward"],data["location"],
            data["category"],data["description"],data.get("duration"),
            data.get("households_affected") or 0,photo_name,data.get("latitude") or None,
            data.get("longitude") or None,data.get("contact_method")
        ))
        conn.commit()
        conn.close()
        return render_template("complaint_success.html", complaint_number=complaint_no)
    return render_template("complaint.html")

@app.route("/track", methods=["GET","POST"])
def track():
    complaint = None
    searched = False
    if request.method == "POST":
        searched = True
        number = request.form.get("complaint_number","").strip().upper()
        conn = db()
        complaint = conn.execute("SELECT * FROM complaints WHERE complaint_number=?", (number,)).fetchone()
        conn.close()
    return render_template("track.html", complaint=complaint, searched=searched)

@app.route("/facilities")
def facilities():
    conn = db()
    rows = conn.execute("SELECT * FROM water_facilities ORDER BY ward, type").fetchall()
    conn.close()
    return render_template("facilities.html", facilities=rows)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password","")
        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

def admin_required():
    return session.get("admin") is True

@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))
    conn = db()
    households = conn.execute("SELECT * FROM households ORDER BY id DESC").fetchall()
    complaints = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    facilities = conn.execute("SELECT * FROM water_facilities ORDER BY id").fetchall()
    stats = {
        "households": len(households),
        "complaints": len(complaints),
        "pending": sum(1 for x in complaints if x["status"] not in ("Resolved","Closed")),
        "resolved": sum(1 for x in complaints if x["status"] == "Resolved"),
        "facilities": len(facilities),
        "nonfunctional": sum(1 for x in facilities if x["status"] == "Not Working")
    }
    conn.close()
    return render_template("admin.html", households=households, complaints=complaints, facilities=facilities, stats=stats)

@app.post("/admin/complaint/<int:complaint_id>/status")
def update_complaint(complaint_id):
    if not admin_required():
        return jsonify({"error":"Unauthorized"}), 401
    status = request.form.get("status")
    remarks = request.form.get("remarks","")
    allowed = {"Submitted","Under Review","Assigned","Work in Progress","Resolved","Closed"}
    if status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin_dashboard"))
    conn = db()
    conn.execute("UPDATE complaints SET status=?, authority_remarks=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                 (status,remarks,complaint_id))
    conn.commit()
    conn.close()
    flash("Complaint updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/export/<kind>")
def export_data(kind):
    if not admin_required():
        return redirect(url_for("admin_login"))
    import csv, io
    conn = db()
    table = "households" if kind == "households" else "complaints"
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(list(row))
    from flask import Response
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={table}.csv"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
