from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


# ========== USER / HR ==========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="employee")  # admin, manager, employee

    # HR ma'lumotlar
    full_name = db.Column(db.String(120))
    position = db.Column(db.String(120))
    phone = db.Column(db.String(64))
    address = db.Column(db.String(200))
    birth_date = db.Column(db.String(20))

    passport_series = db.Column(db.String(10))
    passport_number = db.Column(db.String(20))
    passport_given_date = db.Column(db.String(20))
    passport_given_by = db.Column(db.String(200))

    diploma_type = db.Column(db.String(200))
    diploma_from = db.Column(db.String(200))
    diploma_year = db.Column(db.String(10))

    photo = db.Column(db.String(200))  # avatar fayl nomi

    docs = db.relationship("HRDocument", backref="owner", lazy=True)


class HRDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


# ========== TASHKILOTLAR ==========
class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    employee_count = db.Column(db.Integer)
    address = db.Column(db.String(200))
    floor = db.Column(db.String(50))
    comment = db.Column(db.Text)

    vehicles = db.relationship("Vehicle", backref="organization", lazy=True)


# ========== AVTO TRANSPORT ==========
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(120))
    plate_number = db.Column(db.String(50))
    driver_full_name = db.Column(db.String(120))
    monthly_fuel_limit = db.Column(db.Integer)
    last_repair_date = db.Column(db.String(20))
    photo = db.Column(db.String(200))

    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))


# ========== ORGTEXNIKA ==========
class OrgTech(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    model = db.Column(db.String(128))
    serial_number = db.Column(db.String(128))
    status = db.Column(db.String(64))  # new, working, repair, broken
    comment = db.Column(db.Text)

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")

    last_update = db.Column(db.DateTime, default=datetime.utcnow)


# ========== OUTSOURSING ==========
class OutsourceCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    service_type = db.Column(db.String(128))
    contract_number = db.Column(db.String(64))
    contract_date = db.Column(db.Date)
    contract_amount = db.Column(db.Float, default=0.0)
    comment = db.Column(db.Text)


# ========== SOLAR ==========
class SolarSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    external_url = db.Column(db.String(255))
    location = db.Column(db.String(255))
    capacity_kw = db.Column(db.Float, default=0.0)

    last_power_kw = db.Column(db.Float, default=0.0)
    last_energy_today_kwh = db.Column(db.Float, default=0.0)
    last_updated_at = db.Column(db.DateTime)


class SolarReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("solar_site.id"))
    site = db.relationship("SolarSite", backref="readings")

    date = db.Column(db.Date, default=date.today)
    energy_kwh = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ========== IJRO TOPSHIRIQLARI ==========
class IjroTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    date = db.Column(db.Date)       # kalendarda ko‘rinadigan sana
    due_date = db.Column(db.Date)   # muddat
    status = db.Column(db.String(50), default="new")  # new / in_progress / done / rejected

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")
