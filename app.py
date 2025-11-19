import os
from datetime import date, datetime

from flask import (
    Flask, render_template, redirect, url_for,
    request, session, flash, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import (
    db, User, Task, Vehicle, Organization, OutsourceCompany,
    OrgTech, Contract, SolarSite, EmployeeProfile, IjroTask
)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ------- helpers --------
@app.context_processor
def inject_today():
    return {"today": date.today()}


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
                flash("Bu bo'limga kirish huquqi yo'q", "danger")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static", "img"), "logo_af.png"
    )


# -------- auth ----------
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


# -------- Rahbar paneli (dashboard) ----------
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
    outsourcing_companies = OutsourceCompany.query.order_by(
        OutsourceCompany.id.desc()
    ).limit(3).all()
    total_contract_amount = db.session.query(
        db.func.coalesce(db.func.sum(Contract.amount), 0)
    ).scalar()
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


# ---------- Avtotransportlar (FULL CRUD) ----------
@app.route("/vehicles")
@login_required
def vehicles_list():
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return render_template("vehicles/list.html", vehicles=vehicles)


@app.route("/vehicles/create", methods=["GET", "POST"])
@login_required
def vehicles_create():
    orgs = Organization.query.order_by(Organization.name).all()
    if request.method == "POST":
        plate = request.form.get("plate_number")
        model = request.form.get("model")
        driver = request.form.get("driver_full_name")
        limit = float(request.form.get("monthly_fuel_limit") or 0)
        last_rep_date = request.form.get("last_repair_date") or None
        last_rep_status = request.form.get("last_repair_status")
        org_id = request.form.get("organization_id") or None

        image_file = request.files.get("image")
        image_path = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            image_path = filename

        v = Vehicle(
            plate_number=plate,
            model=model,
            driver_full_name=driver,
            monthly_fuel_limit=limit,
            last_repair_date=datetime.strptime(last_rep_date, "%Y-%m-%d").date()
            if last_rep_date
            else None,
            last_repair_status=last_rep_status,
            organization_id=int(org_id) if org_id else None,
            image_path=image_path,
        )
        db.session.add(v)
        db.session.commit()
        flash("Transport qo'shildi", "success")
        return redirect(url_for("vehicles_list"))
    return render_template("vehicles/form.html", v=None, orgs=orgs)


@app.route("/vehicles/<int:vehicle_id>")
@login_required
def vehicles_detail(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    return render_template("vehicles/detail.html", v=v)


@app.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
def vehicles_edit(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    orgs = Organization.query.order_by(Organization.name).all()
    if request.method == "POST":
        v.plate_number = request.form.get("plate_number")
        v.model = request.form.get("model")
        v.driver_full_name = request.form.get("driver_full_name")
        v.monthly_fuel_limit = float(request.form.get("monthly_fuel_limit") or 0)
        last_rep_date = request.form.get("last_repair_date") or None
        v.last_repair_date = (
            datetime.strptime(last_rep_date, "%Y-%m-%d").date()
            if last_rep_date
            else None
        )
        v.last_repair_status = request.form.get("last_repair_status")
        org_id = request.form.get("organization_id") or None
        v.organization_id = int(org_id) if org_id else None

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            v.image_path = filename

        db.session.commit()
        flash("Transport yangilandi", "success")
        return redirect(url_for("vehicles_detail", vehicle_id=v.id))

    return render_template("vehicles/form.html", v=v, orgs=orgs)


@app.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@login_required
def vehicles_delete(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(v)
    db.session.commit()
    flash("Transport o'chirildi", "success")
    return redirect(url_for("vehicles_list"))


# ---------- Tizim tashkilotlari ----------
@app.route("/organizations")
@login_required
def orgs_list():
    orgs = Organization.query.order_by(Organization.name).all()
    return render_template("orgs/list.html", orgs=orgs)


@app.route("/organizations/create", methods=["GET", "POST"])
@login_required
def orgs_create():
    if request.method == "POST":
        o = Organization(
            name=request.form.get("name"),
            employee_count=int(request.form.get("employee_count") or 0),
            address=request.form.get("address"),
            floor=request.form.get("floor"),
            comment=request.form.get("comment"),
        )
        db.session.add(o)
        db.session.commit()
        flash("Tizim tashkiloti qo'shildi", "success")
        return redirect(url_for("orgs_list"))
    return render_template("orgs/form.html", org=None)


@app.route("/organizations/<int:org_id>", methods=["GET", "POST"])
@login_required
def orgs_detail(org_id):
    org = Organization.query.get_or_404(org_id)
    # shu yerda keyin xodimlar va boshqa bog'lanishlarni ham qo'shamiz
    return render_template("orgs/detail.html", org=org)


# ---------- Ijro moduli (soddalashtirilgan kalendar) ----------
@app.route("/ijro", methods=["GET", "POST"])
@login_required
def ijro_panel():
    # filter: sana bo'yicha
    selected_date = request.args.get("date")
    q = IjroTask.query
    if selected_date:
        try:
            d = datetime.strptime(selected_date, "%Y-%m-%d").date()
            q = q.filter(IjroTask.date == d)
        except ValueError:
            pass
    tasks = q.order_by(IjroTask.date.asc()).all()

    return render_template("ijro/list.html", tasks=tasks, selected_date=selected_date)


@app.route("/ijro/create", methods=["GET", "POST"])
@login_required
@role_required("manager", "admin")
def ijro_create():
    employees = User.query.filter_by(role="employee").all()
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")
        date_str = request.form.get("date")
        due_str = request.form.get("due_date")
        assigned_id = request.form.get("assigned_to_id") or None
        d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
        dd = datetime.strptime(due_str, "%Y-%m-%d").date() if due_str else None

        t = IjroTask(
            title=title,
            description=desc,
            date=d,
            due_date=dd,
            assigned_to_id=int(assigned_id) if assigned_id else None,
        )
        db.session.add(t)
        db.session.commit()
        flash("Ijro topshirig'i yaratildi", "success")
        return redirect(url_for("ijro_panel"))

    return render_template("ijro/form.html", employees=employees)


@app.route("/ijro/<int:task_id>/done", methods=["POST"])
@login_required
def ijro_mark_done(task_id):
    task = IjroTask.query.get_or_404(task_id)
    task.status = "done"
    db.session.commit()
    flash("Topshiriq bajarildi deb belgilandi", "success")
    return redirect(url_for("ijro_panel"))


# ---------- Admin / Employee / boshqa modullar (placeholder) ----------
@app.route("/admin/panel")
@login_required
@role_required("admin")
def admin_panel():
    return render_template("admin/dashboard.html")


@app.route("/employee/panel")
@login_required
@role_required("employee", "manager", "admin")
def employee_panel():
    return render_template("employee/dashboard.html")


@app.route("/outsourcing")
@login_required
def outsourcing_panel():
    companies = OutsourceCompany.query.all()
    return render_template("outsourcing/list.html", companies=companies)


@app.route("/orgtech")
@login_required
def orgtech_panel():
    devices = OrgTech.query.all()
    return render_template("orgtech/list.html", devices=devices)


@app.route("/contracts")
@login_required
def contracts_list():
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    return render_template("contracts/list.html", contracts=contracts)


@app.route("/hr")
@login_required
def hr_panel():
    employees = User.query.filter_by(role="employee").all()
    profiles = EmployeeProfile.query.all()
    return render_template("hr/users.html", employees=employees, profiles=profiles)


@app.route("/solar")
@login_required
def solar_panel():
    sites = SolarSite.query.all()
    return render_template("solar/dashboard.html", sites=sites)


# ---------- DB init ----------
with app.app_context():
    db.create_all()
    changed = False
    if not User.query.filter_by(username="admin").first():
        db.session.add(
            User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="admin",
            )
        )
        changed = True
    if not User.query.filter_by(username="manager").first():
        db.session.add(
            User(
                username="manager",
                password_hash=generate_password_hash("manager123"),
                role="manager",
            )
        )
        changed = True
    if not User.query.filter_by(username="employee").first():
        db.session.add(
            User(
                username="employee",
                password_hash=generate_password_hash("employee123"),
                role="employee",
            )
        )
        changed = True
    if changed:
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
