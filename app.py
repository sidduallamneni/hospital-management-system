"""Hospital Management System - Cloud Computing Lab Project.

A containerised Flask web app + REST API with SQLite storage.
Configuration comes from environment variables (12-factor style) so the
same image runs on a laptop, AWS, Azure, GCP or Kubernetes.
"""
import os
import sqlite3
from datetime import datetime

from flask import Flask, g, jsonify, redirect, render_template, request, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["DB_PATH"] = os.environ.get("DB_PATH", "hms.db")

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS patients(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER,
  gender TEXT, phone TEXT, address TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS doctors(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
  specialization TEXT, phone TEXT, fee REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS appointments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
  date TEXT, time TEXT, reason TEXT, status TEXT DEFAULT 'Scheduled');
CREATE TABLE IF NOT EXISTS bills(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  description TEXT, amount REAL, status TEXT DEFAULT 'Unpaid', created_at TEXT);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(app.config["DB_PATH"])
    db.executescript(SCHEMA)
    db.commit()
    db.close()


def q(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def run(sql, args=()):
    db = get_db()
    db.execute(sql, args)
    db.commit()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------------- Health & Dashboard ----------------
@app.route("/health")
def health():
    """Used by load balancers / Kubernetes liveness & readiness probes."""
    try:
        q("SELECT 1")
        return jsonify(status="ok", time=now()), 200
    except Exception as e:  # pragma: no cover
        return jsonify(status="error", detail=str(e)), 500


def stats():
    return {
        "patients": q("SELECT COUNT(*) c FROM patients", one=True)["c"],
        "doctors": q("SELECT COUNT(*) c FROM doctors", one=True)["c"],
        "appointments": q("SELECT COUNT(*) c FROM appointments", one=True)["c"],
        "unpaid": q("SELECT COALESCE(SUM(amount),0) s FROM bills WHERE status='Unpaid'", one=True)["s"],
        "revenue": q("SELECT COALESCE(SUM(amount),0) s FROM bills WHERE status='Paid'", one=True)["s"],
    }


@app.route("/")
def index():
    upcoming = q("""SELECT a.*, p.name patient, d.name doctor FROM appointments a
                    JOIN patients p ON p.id=a.patient_id JOIN doctors d ON d.id=a.doctor_id
                    WHERE a.status='Scheduled' ORDER BY a.date, a.time LIMIT 5""")
    return render_template("index.html", s=stats(), upcoming=upcoming)


# ---------------- Patients ----------------
@app.route("/patients", methods=["GET", "POST"])
def patients():
    if request.method == "POST":
        f = request.form
        if not f.get("name", "").strip():
            flash("Patient name is required.", "error")
        else:
            run("INSERT INTO patients(name,age,gender,phone,address,created_at) VALUES(?,?,?,?,?,?)",
                (f["name"].strip(), f.get("age") or None, f.get("gender"), f.get("phone"), f.get("address"), now()))
            flash("Patient added.", "ok")
        return redirect(url_for("patients"))
    search = request.args.get("q", "")
    rows = q("SELECT * FROM patients WHERE name LIKE ? ORDER BY id DESC", (f"%{search}%",))
    return render_template("patients.html", rows=rows, search=search)


@app.route("/patients/<int:pid>/delete", methods=["POST"])
def delete_patient(pid):
    run("DELETE FROM patients WHERE id=?", (pid,))
    flash("Patient deleted.", "ok")
    return redirect(url_for("patients"))


# ---------------- Doctors ----------------
@app.route("/doctors", methods=["GET", "POST"])
def doctors():
    if request.method == "POST":
        f = request.form
        if not f.get("name", "").strip():
            flash("Doctor name is required.", "error")
        else:
            run("INSERT INTO doctors(name,specialization,phone,fee) VALUES(?,?,?,?)",
                (f["name"].strip(), f.get("specialization"), f.get("phone"), f.get("fee") or 0))
            flash("Doctor added.", "ok")
        return redirect(url_for("doctors"))
    return render_template("doctors.html", rows=q("SELECT * FROM doctors ORDER BY id DESC"))


@app.route("/doctors/<int:did>/delete", methods=["POST"])
def delete_doctor(did):
    run("DELETE FROM doctors WHERE id=?", (did,))
    flash("Doctor deleted.", "ok")
    return redirect(url_for("doctors"))


# ---------------- Appointments ----------------
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        f = request.form
        clash = q("SELECT 1 FROM appointments WHERE doctor_id=? AND date=? AND time=? AND status!='Cancelled'",
                  (f["doctor_id"], f["date"], f["time"]), one=True)
        if clash:
            flash("Doctor already has an appointment at that time.", "error")
        else:
            run("INSERT INTO appointments(patient_id,doctor_id,date,time,reason) VALUES(?,?,?,?,?)",
                (f["patient_id"], f["doctor_id"], f["date"], f["time"], f.get("reason")))
            flash("Appointment booked.", "ok")
        return redirect(url_for("appointments"))
    rows = q("""SELECT a.*, p.name patient, d.name doctor FROM appointments a
                JOIN patients p ON p.id=a.patient_id JOIN doctors d ON d.id=a.doctor_id
                ORDER BY a.date DESC, a.time DESC""")
    return render_template("appointments.html", rows=rows,
                           patients=q("SELECT id,name FROM patients ORDER BY name"),
                           doctors=q("SELECT id,name,specialization FROM doctors ORDER BY name"))


@app.route("/appointments/<int:aid>/status", methods=["POST"])
def appointment_status(aid):
    status = request.form.get("status", "Scheduled")
    if status in ("Scheduled", "Completed", "Cancelled"):
        run("UPDATE appointments SET status=? WHERE id=?", (status, aid))
    return redirect(url_for("appointments"))


@app.route("/appointments/<int:aid>/delete", methods=["POST"])
def delete_appointment(aid):
    run("DELETE FROM appointments WHERE id=?", (aid,))
    return redirect(url_for("appointments"))


# ---------------- Billing ----------------
@app.route("/billing", methods=["GET", "POST"])
def billing():
    if request.method == "POST":
        f = request.form
        try:
            amount = float(f["amount"])
        except (KeyError, ValueError):
            flash("Enter a valid amount.", "error")
            return redirect(url_for("billing"))
        run("INSERT INTO bills(patient_id,description,amount,created_at) VALUES(?,?,?,?)",
            (f["patient_id"], f.get("description"), amount, now()))
        flash("Bill generated.", "ok")
        return redirect(url_for("billing"))
    rows = q("""SELECT b.*, p.name patient FROM bills b JOIN patients p ON p.id=b.patient_id
                ORDER BY b.id DESC""")
    return render_template("billing.html", rows=rows, patients=q("SELECT id,name FROM patients ORDER BY name"))


@app.route("/billing/<int:bid>/pay", methods=["POST"])
def pay_bill(bid):
    run("UPDATE bills SET status='Paid' WHERE id=?", (bid,))
    flash("Bill marked as paid.", "ok")
    return redirect(url_for("billing"))


# ---------------- REST API ----------------
@app.route("/api/stats")
def api_stats():
    return jsonify(stats())


@app.route("/api/patients", methods=["GET", "POST"])
def api_patients():
    if request.method == "POST":
        d = request.get_json(silent=True) or {}
        if not d.get("name"):
            return jsonify(error="name is required"), 400
        run("INSERT INTO patients(name,age,gender,phone,address,created_at) VALUES(?,?,?,?,?,?)",
            (d["name"], d.get("age"), d.get("gender"), d.get("phone"), d.get("address"), now()))
        return jsonify(message="created"), 201
    return jsonify([dict(r) for r in q("SELECT * FROM patients")])


@app.route("/api/doctors")
def api_doctors():
    return jsonify([dict(r) for r in q("SELECT * FROM doctors")])


@app.route("/api/appointments")
def api_appointments():
    return jsonify([dict(r) for r in q("SELECT * FROM appointments")])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("DEBUG") == "1")
