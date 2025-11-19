from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

# ================== MODELS =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="employee")
    telegram_chat_id = db.Column(db.String(64))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default="new")  # new, in_progress, done, rejected
    priority = db.Column(db.String(16), default="normal")
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    employee_count = db.Column(db.Integer, default=0)
    address = db.Column(db.String(255))
    floor = db.Column(db.String(64))
    comment = db.Column(db.Text)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(32), unique=True)
    model = db.Column(db.String(64))
    driver_full_name = db.Column(db.String(128))
    monthly_fuel_limit = db.Column(db.Float, default=0.0)
    last_repair_date = db.Column(db.Date)
    last_repair_status = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    organization = db.relationship("Organization", backref="vehicles")


class OutsourceCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    service_type = db.Column(db.String(128))
    contract_number = db.Column(db.String(64))
    contract_date = db.Column(db.Date)
    contract_amount = db.Column(db.Float)
    comment = db.Column(db.Text)


class OutsourceEmployee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128))
    position = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    company_id = db.Column(db.Integer, db.ForeignKey("outsource_company.id"))
    company = db.relationship("OutsourceCompany", backref="employees")


class OrgTech(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    model = db.Column(db.String(128))
    serial_number = db.Column(db.String(128))
    status = db.Column(db.String(64))  # new, working, repair, broken
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")
    last_update = db.Column(db.DateTime, default=datetime.utcnow)


class SolarSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    external_url = db.Column(db.String(255))
    capacity_kw = db.Column(db.Float, default=0.0)


class SolarReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("solar_site.id"))
    site = db.relationship("SolarSite", backref="readings")
    date = db.Column(db.Date, default=date.today)
    energy_kwh = db.Column(db.Float, default=0.0)


class EmployeeProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    passport_number = db.Column(db.String(32))
    diploma_info = db.Column(db.String(255))
    other_info = db.Column(db.Text)


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class IjroTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(32), default="new")  # new, in_progress, done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================== APP FACTORY =====================

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.before_request
    def load_user_role():
        # helper to ensure session keys exist
        session.setdefault("user_id", None)
        session.setdefault("user_role", None)

    # ---------- Auth ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["user_id"] = user.id
                session["user_role"] = user.role
                flash("Xush kelibsiz, %s!" % user.username, "success")
                return redirect(url_for("index"))
            flash("Login yoki parol noto'g'ri", "danger")
        return render_template("auth/login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Tizimdan chiqdingiz", "info")
        return redirect(url_for("login"))

    # ---------- Index redirect ----------
    @app.route("/")
    def index():
        role = session.get("user_role")
        if role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif role == "manager":
            return redirect(url_for("manager_dashboard"))
        elif role == "employee":
            return redirect(url_for("employee_dashboard"))
        else:
            return redirect(url_for("login"))

    # ---------- Simple role-required decorator ----------
    from functools import wraps

    def role_required(*roles):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                if session.get("user_role") not in roles:
                    flash("Sizda ushbu bo'limga kirish huquqi yo'q", "danger")
                    return redirect(url_for("login"))
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    # ---------- Dashboards ----------
    @app.route("/admin/dashboard")
    @role_required("admin")
    def admin_dashboard():
        user_count = User.query.count()
        task_count = Task.query.count()
        contract_sum = db.session.query(db.func.coalesce(db.func.sum(Contract.amount), 0)).scalar()
        return render_template("admin/dashboard.html",
                               user_count=user_count,
                               task_count=task_count,
                               contract_sum=contract_sum)

    @app.route("/manager/dashboard")
    @role_required("manager")
    def manager_dashboard():
        tasks = Task.query.order_by(Task.created_at.desc()).limit(20).all()
        vehicles = Vehicle.query.limit(4).all()
        contracts = Contract.query.order_by(Contract.created_at.desc()).limit(5).all()
        outsourcing_companies = OutsourceCompany.query.limit(3).all()
        active_employees = User.query.filter_by(role="employee").count()

        new_tasks = Task.query.filter_by(status="new").count()
        in_progress = Task.query.filter_by(status="in_progress").count()
        done_tasks = Task.query.filter_by(status="done").count()
        total_contract_amount = db.session.query(db.func.coalesce(db.func.sum(Contract.amount), 0)).scalar()

        return render_template("manager/dashboard.html",
                               tasks=tasks,
                               vehicles=vehicles,
                               contracts=contracts,
                               outsourcing_companies=outsourcing_companies,
                               active_employees=active_employees,
                               new_tasks=new_tasks,
                               in_progress=in_progress,
                               done_tasks=done_tasks,
                               total_contract_amount=total_contract_amount)

    @app.route("/employee/dashboard")
    @role_required("employee")
    def employee_dashboard():
        user_id = session.get("user_id")
        my_tasks = Task.query.filter_by(assigned_to_id=user_id).all()
        ijro = IjroTask.query.filter_by(assigned_to_id=user_id).all()
        profile = EmployeeProfile.query.filter_by(user_id=user_id).first()
        return render_template("employee/dashboard.html",
                               my_tasks=my_tasks,
                               ijro=ijro,
                               profile=profile)

    # ---------- Vehicles ----------
    @app.route("/vehicles")
    @role_required("manager", "admin")
    def vehicles_list():
        vehicles = Vehicle.query.all()
        return render_template("vehicles/list.html", vehicles=vehicles)

    @app.route("/vehicles/create", methods=["GET", "POST"])
    @role_required("manager", "admin")
    def vehicles_create():
        orgs = Organization.query.order_by(Organization.name).all()
        if request.method == "POST":
            v = Vehicle(
                plate_number=request.form.get("plate_number"),
                model=request.form.get("model"),
                driver_full_name=request.form.get("driver_full_name"),
                monthly_fuel_limit=float(request.form.get("monthly_fuel_limit") or 0),
                last_repair_status=request.form.get("last_repair_status") or None,
                organization_id=int(request.form.get("organization_id")) if request.form.get("organization_id") else None,
            )
            db.session.add(v)
            db.session.commit()
            flash("Transport qo'shildi", "success")
            return redirect(url_for("vehicles_list"))
        return render_template("vehicles/form.html", orgs=orgs)

    @app.route("/vehicles/<int:vehicle_id>")
    @role_required("manager", "admin")
    def vehicles_detail(vehicle_id):
        v = Vehicle.query.get_or_404(vehicle_id)
        return render_template("vehicles/detail.html", v=v)

    # ---------- Organizations ----------
    @app.route("/organizations")
    @role_required("manager", "admin")
    def orgs_list():
        orgs = Organization.query.order_by(Organization.name).all()
        return render_template("orgs/list.html", orgs=orgs)

    @app.route("/organizations/create", methods=["GET", "POST"])
    @role_required("manager", "admin")
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

    @app.route("/organizations/<int:org_id>")
    @role_required("manager", "admin")
    def orgs_detail(org_id):
        org = Organization.query.get_or_404(org_id)
        vehicles = Vehicle.query.filter_by(organization_id=org.id).all()
        return render_template("orgs/detail.html", org=org, vehicles=vehicles)

    # ---------- Outsourcing ----------
    @app.route("/outsourcing")
    @role_required("manager", "admin")
    def outsourcing_list():
        companies = OutsourceCompany.query.order_by(OutsourceCompany.name).all()
        return render_template("outsourcing/list.html", companies=companies)

    @app.route("/outsourcing/create", methods=["GET", "POST"])
    @role_required("manager", "admin")
    def outsourcing_create():
        if request.method == "POST":
            c = OutsourceCompany(
                name=request.form.get("name"),
                service_type=request.form.get("service_type"),
                contract_number=request.form.get("contract_number"),
                contract_amount=float(request.form.get("contract_amount") or 0),
                comment=request.form.get("comment"),
            )
            db.session.add(c)
            db.session.commit()
            flash("Outsorsing tashkiloti qo'shildi", "success")
            return redirect(url_for("outsourcing_list"))
        return render_template("outsourcing/form.html")

    # ---------- Orgtech ----------
    @app.route("/orgtech")
    @role_required("manager", "admin")
    def orgtech_list():
        devices = OrgTech.query.all()
        return render_template("orgtech/list.html", devices=devices)

    @app.route("/orgtech/create", methods=["GET", "POST"])
    @role_required("manager", "admin")
    def orgtech_create():
        users = User.query.order_by(User.username).all()
        if request.method == "POST":
            d = OrgTech(
                name=request.form.get("name"),
                model=request.form.get("model"),
                serial_number=request.form.get("serial_number"),
                status=request.form.get("status") or "new",
                assigned_to_id=int(request.form.get("assigned_to_id")) if request.form.get("assigned_to_id") else None,
            )
            db.session.add(d)
            db.session.commit()
            flash("Orgtexnika qo'shildi", "success")
            return redirect(url_for("orgtech_list"))
        return render_template("orgtech/form.html", users=users)

    # ---------- Contracts (simple) ----------
    @app.route("/contracts")
    @role_required("manager", "admin")
    def contracts_list():
        contracts = Contract.query.order_by(Contract.created_at.desc()).all()
        return render_template("contracts/list.html", contracts=contracts)

    # ---------- HR / Users ----------
    @app.route("/hr/users")
    @role_required("manager", "admin")
    def hr_users():
        users = User.query.all()
        return render_template("hr/users.html", users=users)

    # ---------- Ijro (calendar placeholder) ----------
    @app.route("/ijro")
    @role_required("manager", "admin", "employee")
    def ijro_list():
        ijro_tasks = IjroTask.query.order_by(IjroTask.due_date.asc()).all()
        return render_template("ijro/calendar.html", ijro_tasks=ijro_tasks)

    # ---------- Solar (simple) ----------
    @app.route("/solar")
    @role_required("manager", "admin")
    def solar_dashboard():
        sites = SolarSite.query.all()
        return render_template("solar/dashboard.html", sites=sites)

    # ---------- CLI helper to init db ----------
    @app.cli.command("init-db")
    def init_db():
        db.drop_all()
        db.create_all()
        # default users
        admin = User(username="admin", role="admin"); admin.set_password("admin123")
        manager = User(username="manager", role="manager"); manager.set_password("manager123")
        employee = User(username="employee", role="employee"); employee.set_password("employee123")
        db.session.add_all([admin, manager, employee])
        db.session.commit()
        print("DB initialized with default users.")

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # ensure default users exist
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="admin")
            admin.set_password("admin123")
            manager = User(username="manager", role="manager")
            manager.set_password("manager123")
            employee = User(username="employee", role="employee")
            employee.set_password("employee123")
            db.session.add_all([admin, manager, employee])
            db.session.commit()
    app.run(debug=True)
