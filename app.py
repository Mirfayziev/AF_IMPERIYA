import os
import json
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from sqlalchemy import func

from models import db, User, HRDocument, Organization, Vehicle, OrgTech, OutsourceCompany, SolarSite, SolarReading, IjroTask

app = Flask(__name__)

app.config["SECRET_KEY"] = "super-secret-af-imperiya"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
db.init_app(app)


# ---------- HELPERS ----------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ---------- INIT DB & DEFAULT ADMIN ----------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password="admin",
            role="admin",
            full_name="Super Admin"
        )
        db.session.add(admin)
        db.session.commit()



# ---------- LOGIN ----------

@app.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        if session.get("user_role") == "admin":
            return redirect(url_for("admin_dashboard"))
        elif session.get("user_role") == "manager":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("employee_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session["user_id"] = user.id
            session["username"] = user.username
            session["user_role"] = user.role
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "manager":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("employee_dashboard"))
    # login.html oldin bergan dizayn bilan
    now = datetime.now()
    return render_template("login.html", now=now)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- ADMIN DASHBOARD ----------

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("login"))

    total_employees = User.query.filter_by(role="employee").count()
    active_tasks = IjroTask.query.filter(IjroTask.status != "done").count()
    vehicles_count = Vehicle.query.count()
    outsource_count = OutsourceCompany.query.count()
    solar_today = db.session.query(func.coalesce(func.sum(SolarReading.energy_kwh), 0)).filter(
        SolarReading.date == date.today()
    ).scalar()

    task_status_data = {
        "labels": ["new", "in_progress", "done"],
        "values": [
            IjroTask.query.filter_by(status="new").count(),
            IjroTask.query.filter_by(status="in_progress").count(),
            IjroTask.query.filter_by(status="done").count(),
        ],
    }

    today = date.today()
    solar_labels = []
    solar_values = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        solar_labels.append(d.isoformat())
        total_kwh = db.session.query(func.coalesce(func.sum(SolarReading.energy_kwh), 0)).filter(
            SolarReading.date == d
        ).scalar()
        solar_values.append(float(total_kwh or 0))

    ijro_monthly_data = {
        "labels": [],
        "values": [],
    }

    return render_template(
        "admin/dashboard.html",
        total_employees=total_employees,
        active_tasks=active_tasks,
        vehicles_count=vehicles_count,
        outsource_count=outsource_count,
        solar_today_kwh=solar_today or 0,
        task_status_data=json.dumps(task_status_data),
        ijro_monthly_data=json.dumps(ijro_monthly_data),
        solar_weekly_data=json.dumps(
            {"labels": solar_labels, "values": solar_values}
        ),
    )


# ---------- EMPLOYEE DASHBOARD ----------

@app.route("/employee/dashboard")
@login_required
def employee_dashboard():
    if session.get("user_role") != "employee":
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    u = User.query.get_or_404(user_id)

    today = date.today()
    tasks_today = IjroTask.query.filter(
        IjroTask.assigned_to_id == user_id,
        IjroTask.date == today,
    ).all()
    today_tasks = len(tasks_today)

    new_tasks = IjroTask.query.filter_by(
        assigned_to_id=user_id, status="new"
    ).count()
    completed_tasks = IjroTask.query.filter_by(
        assigned_to_id=user_id, status="done"
    ).count()

    employee_modules = ["ijro", "vehicles", "orgtech", "hr"]

    mini_calendar = "Kalendar tez orada to‘liq integratsiya qilinadi."

    return render_template(
        "employee/dashboard.html",
        today_tasks=today_tasks,
        new_tasks=new_tasks,
        completed_tasks=completed_tasks,
        employee_modules=employee_modules,
        today_task_list=tasks_today,
        mini_calendar=mini_calendar,
    )


# ---------- VEHICLES ----------

@app.route("/vehicles")
@login_required
def vehicle_list():
    vehicles = Vehicle.query.all()
    return render_template("vehicles/list.html", vehicles=vehicles)


@app.route("/vehicles/create", methods=["GET", "POST"])
@login_required
def vehicle_create():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("vehicle_list"))

    if request.method == "POST":
        model = request.form.get("model")
        plate = request.form.get("plate_number")
        driver = request.form.get("driver_full_name")
        limit = request.form.get("monthly_fuel_limit") or 0
        repair = request.form.get("last_repair_date")

        file = request.files.get("photo")
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        v = Vehicle(
            model=model,
            plate_number=plate,
            driver_full_name=driver,
            monthly_fuel_limit=int(limit),
            last_repair_date=repair,
            photo=filename,
        )
        db.session.add(v)
        db.session.commit()
        return redirect(url_for("vehicle_list"))

    return render_template("vehicles/create.html")


@app.route("/vehicles/<int:vehicle_id>")
@login_required
def vehicle_details(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    return render_template("vehicles/details.html", vehicle=v)


# ---------- ORGTECH ----------

@app.route("/orgtech")
@login_required
def orgtech_list():
    items = OrgTech.query.all()
    return render_template("orgtech/list.html", items=items)


@app.route("/orgtech/create", methods=["GET", "POST"])
@login_required
def orgtech_create():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("orgtech_list"))

    users = User.query.all()
    if request.method == "POST":
        t = OrgTech(
            name=request.form.get("name"),
            model=request.form.get("model"),
            serial_number=request.form.get("serial_number"),
            status=request.form.get("status"),
            comment=request.form.get("comment"),
        )
        assigned_id = request.form.get("assigned_to")
        if assigned_id:
            t.assigned_to_id = int(assigned_id)
        db.session.add(t)
        db.session.commit()
        return redirect(url_for("orgtech_list"))

    return render_template("orgtech/create.html", users=users)


@app.route("/orgtech/<int:item_id>")
@login_required
def orgtech_details(item_id):
    item = OrgTech.query.get_or_404(item_id)
    return render_template("orgtech/details.html", item=item)


# ---------- ORGANIZATIONS ----------

@app.route("/organizations")
@login_required
def organizations_list():
    organizations = Organization.query.all()
    return render_template("organizations/list.html", organizations=organizations)


@app.route("/organizations/create", methods=["GET", "POST"])
@login_required
def organizations_create():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("organizations_list"))

    if request.method == "POST":
        org = Organization(
            name=request.form.get("name"),
            employee_count=request.form.get("employee_count") or 0,
            address=request.form.get("address"),
            floor=request.form.get("floor"),
            comment=request.form.get("comment"),
        )
        db.session.add(org)
        db.session.commit()
        return redirect(url_for("organizations_list"))

    return render_template("organizations/create.html")


@app.route("/organizations/<int:org_id>")
@login_required
def organizations_details(org_id):
    org = Organization.query.get_or_404(org_id)
    return render_template("organizations/details.html", org=org)


# ---------- OUTSOURSING ----------

@app.route("/outsourcing")
@login_required
def outsourcing_list():
    companies = OutsourceCompany.query.all()
    return render_template("outsourcing/list.html", companies=companies)


@app.route("/outsourcing/create", methods=["GET", "POST"])
@login_required
def outsourcing_create():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("outsourcing_list"))

    if request.method == "POST":
        from datetime import datetime as dt

        date_str = request.form.get("contract_date")
        cdate = None
        if date_str:
            try:
                cdate = dt.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                cdate = None

        comp = OutsourceCompany(
            name=request.form.get("name"),
            service_type=request.form.get("service_type"),
            contract_number=request.form.get("contract_number"),
            contract_date=cdate,
            contract_amount=float(request.form.get("contract_amount") or 0),
            comment=request.form.get("comment"),
        )
        db.session.add(comp)
        db.session.commit()
        return redirect(url_for("outsourcing_list"))

    return render_template("outsourcing/create.html")


@app.route("/outsourcing/<int:company_id>")
@login_required
def outsourcing_details(company_id):
    company = OutsourceCompany.query.get_or_404(company_id)
    return render_template("outsourcing/details.html", company=company)


# ---------- SOLAR ----------

@app.route("/solar")
@login_required
def solar_dashboard():
    sites = SolarSite.query.all()
    total_power_kw = sum(s.last_power_kw or 0 for s in sites)
    total_energy_today_kwh = sum(s.last_energy_today_kwh or 0 for s in sites)

    today = date.today()
    labels = []
    values = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.isoformat())
        total_kwh = db.session.query(func.coalesce(func.sum(SolarReading.energy_kwh), 0)).filter(
            SolarReading.date == d
        ).scalar()
        values.append(float(total_kwh or 0))

    return render_template(
        "solar/dashboard.html",
        sites=sites,
        total_power_kw=total_power_kw,
        total_energy_today_kwh=total_energy_today_kwh,
        chart_labels=json.dumps(labels),
        chart_values=json.dumps(values),
    )


@app.route("/solar/<int:site_id>")
@login_required
def solar_detail(site_id):
    site = SolarSite.query.get_or_404(site_id)
    readings = (
        SolarReading.query.filter_by(site_id=site.id)
        .order_by(SolarReading.date.desc())
        .limit(14)
        .all()
    )
    readings = list(reversed(readings))
    labels = [r.date.isoformat() for r in readings]
    values = [float(r.energy_kwh or 0) for r in readings]

    return render_template(
        "solar/site_detail.html",
        site=site,
        readings=readings,
        chart_labels=json.dumps(labels),
        chart_values=json.dumps(values),
    )


# ---------- IJRO ----------

@app.route("/ijro")
@login_required
def ijro_list():
    tasks = IjroTask.query.order_by(IjroTask.date.asc()).all()
    return render_template("ijro/list.html", tasks=tasks)


@app.route("/ijro/create", methods=["GET", "POST"])
@login_required
def ijro_create():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("ijro_list"))

    employees = User.query.filter_by(role="employee").all()
    if request.method == "POST":
        from datetime import datetime as dt

        title = request.form.get("title")
        desc = request.form.get("description")
        due = request.form.get("due_date")
        assigned = request.form.get("assigned_to")

        today = date.today()
        d_due = None
        if due:
            try:
                d_due = dt.strptime(due, "%Y-%m-%d").date()
            except Exception:
                d_due = None

        task = IjroTask(
            title=title,
            description=desc,
            date=today,
            due_date=d_due,
            status="new",
        )
        if assigned:
            task.assigned_to_id = int(assigned)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for("ijro_list"))

    return render_template("ijro/create.html", employees=employees)


@app.route("/ijro/done/<int:task_id>")
@login_required
def ijro_done(task_id):
    t = IjroTask.query.get_or_404(task_id)
    # faqat xuddi o'ziga tegishli bo'lsa yoki admin/manager bo‘lsa
    if session.get("user_role") == "employee" and t.assigned_to_id != session.get("user_id"):
        return redirect(url_for("ijro_list"))
    t.status = "done"
    db.session.commit()
    return redirect(url_for("ijro_list"))


@app.route("/ijro/calendar")
@login_required
def ijro_calendar():
    tasks = IjroTask.query.all()
    tasks_json = [
        {
            "title": t.title,
            "description": t.description or "",
            "date": t.date.isoformat() if t.date else "",
            "due_date": t.due_date.isoformat() if t.due_date else "",
            "status": t.status or "new",
        }
        for t in tasks
    ]
    return render_template("ijro/calendar.html", tasks_json=json.dumps(tasks_json))


# ---------- HR ----------

@app.route("/hr/list")
@login_required
def hr_list():
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("login"))
    users = User.query.filter(User.role != "admin").all()
    return render_template("hr/list.html", users=users)


@app.route("/hr/profile/<int:user_id>")
@login_required
def hr_profile(user_id):
    # Employee o‘zi faqat o‘z profilini ko‘radi
    if session.get("user_role") == "employee" and session.get("user_id") != user_id:
        return redirect(url_for("employee_dashboard"))
    u = User.query.get_or_404(user_id)
    return render_template("hr/profile.html", user=u)


@app.route("/hr/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
def hr_edit(user_id):
    if session.get("user_role") not in ["admin", "manager"]:
        return redirect(url_for("login"))

    u = User.query.get_or_404(user_id)

    if request.method == "POST":
        u.full_name = request.form.get("full_name")
        u.position = request.form.get("position")
        u.phone = request.form.get("phone")
        u.address = request.form.get("address")
        u.birth_date = request.form.get("birth_date")

        u.passport_series = request.form.get("passport_series")
        u.passport_number = request.form.get("passport_number")
        u.passport_given_date = request.form.get("passport_given_date")
        u.passport_given_by = request.form.get("passport_given_by")

        u.diploma_type = request.form.get("diploma_type")
        u.diploma_from = request.form.get("diploma_from")
        u.diploma_year = request.form.get("diploma_year")

        photo = request.files.get("photo")
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            u.photo = filename

        docs_files = request.files.getlist("docs")
        for f in docs_files:
            if f and f.filename:
                fname = secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                doc = HRDocument(filename=fname, owner=u)
                db.session.add(doc)

        db.session.commit()
        return redirect(url_for("hr_profile", user_id=user_id))

    return render_template("hr/edit.html", user=u)


# ---------- MAIN ----------

if __name__ == "__main__":
    app.run(debug=True)
