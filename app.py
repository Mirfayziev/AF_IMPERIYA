import os
from datetime import date
from flask import Flask, render_template, redirect, url_for, request, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Task, Vehicle, Organization, OutsourceCompany, OrgTech, Contract, SolarSite, EmployeeProfile, IjroTask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.context_processor
def inject_today():
    return {"today": date.today()}

# ---- auth utils ----
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    from functools import wraps
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("user_role") not in roles:
                flash("Sizda bu bo'limga kirish huquqi yo'q", "danger")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static", "img"), "logo_af.png")

@app.route("/")
def index():
    role = session.get("user_role")
    if role == "manager":
        return redirect(url_for("manager_dashboard"))
    if role == "admin":
        return redirect(url_for("admin_panel"))
    if role == "employee":
        return redirect(url_for("employee_panel"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_role"] = user.role
            return redirect(url_for("index"))
        flash("Login yoki parol noto'g'ri", "danger")
    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Rahbar paneli (rasmga o‘xshash premium dashboard) ----------
@app.route("/manager/dashboard")
@login_required
@role_required("manager", "admin")
def manager_dashboard():
    tasks = Task.query.order_by(Task.due_date.asc().nullslast()).all()
    new_tasks = Task.query.filter_by(status="new").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done_tasks = Task.query.filter_by(status="done").count()

    vehicles = Vehicle.query.limit(4).all()
    contracts = Contract.query.order_by(Contract.created_at.desc()).limit(5).all()
    outsourcing_companies = OutsourceCompany.query.order_by(OutsourceCompany.id.desc()).limit(3).all()
    total_contract_amount = db.session.query(db.func.coalesce(db.func.sum(Contract.amount), 0)).scalar()
    active_employees = User.query.filter_by(role="employee").count()

    return render_template(
        "manager/dashboard.html",
        tasks=tasks,
        new_tasks=new_tasks,
        in_progress=in_progress,
        done_tasks=done_tasks,
        vehicles=vehicles,
        contracts=contracts,
        outsourcing_companies=outsourcing_companies,
        total_contract_amount=total_contract_amount,
        active_employees=active_employees,
    )

# --------- qolgan modullarni keyin to‘ldiramiz (hozir senga asosiylari kifoya) ---------

@app.route("/admin")
@login_required
@role_required("admin")
def admin_panel():
    return render_template("admin/dashboard.html")

@app.route("/employee")
@login_required
@role_required("employee", "manager", "admin")
def employee_panel():
    return render_template("employee/dashboard.html")

# DB init (demo userlar)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password_hash=generate_password_hash("admin123"), role="admin"))
    if not User.query.filter_by(username="manager").first():
        db.session.add(User(username="manager", password_hash=generate_password_hash("manager123"), role="manager"))
    if not User.query.filter_by(username="employee").first():
        db.session.add(User(username="employee", password_hash=generate_password_hash("employee123"), role="employee"))
    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
