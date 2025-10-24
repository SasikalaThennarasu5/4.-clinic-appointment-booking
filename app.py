from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clinic.db"
db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_doctor = db.Column(db.Boolean, default=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ ROUTES ------------------
@app.route("/")
def index():
    doctors = User.query.filter_by(is_doctor=True).all()
    return render_template("index.html", doctors=doctors)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        is_doctor = "is_doctor" in request.form
        user = User(username=username, email=email, password=password, is_doctor=is_doctor)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["is_doctor"] = user.is_doctor
            session["username"] = user.username
            flash("Login successful!", "success")
            if user.is_doctor:
                return redirect(url_for("doctor_dashboard"))
            return redirect(url_for("index"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))

@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
def book_appointment(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    if request.method == "POST":
        patient_name = session.get("username", "Anonymous")
        date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
        time = datetime.strptime(request.form["time"], "%H:%M").time()
        appointment = Appointment(doctor_id=doctor.id, patient_name=patient_name, date=date, time=time)
        db.session.add(appointment)
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for("index"))
    return render_template("book_appointment.html", doctor=doctor)

@app.route("/doctor/dashboard")
def doctor_dashboard():
    if not session.get("is_doctor"):
        flash("Access denied", "danger")
        return redirect(url_for("index"))
    doctor_id = session["user_id"]
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.date).all()
    return render_template("doctor_dashboard.html", appointments=appointments)

# ------------------ MAIN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # ✅ replaces @app.before_first_request
    app.run(debug=True)
