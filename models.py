from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="employee")  # admin / manager / employee

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default="new")  # new / in_progress / done / rejected
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
    name = db.Column(db.String(128))
    service_type = db.Column(db.String(128))
    contract_number = db.Column(db.String(64))
    contract_date = db.Column(db.Date)
    contract_amount = db.Column(db.Float)
    comment = db.Column(db.Text)

class OrgTech(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    model = db.Column(db.String(128))
    serial_number = db.Column(db.String(128))
    status = db.Column(db.String(64))  # new / working / repair / broken
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")
    last_update = db.Column(db.DateTime, default=datetime.utcnow)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    full_name = db.Column(db.String(128))
    passport_info = db.Column(db.String(255))
    diploma_info = db.Column(db.String(255))
    other_docs = db.Column(db.Text)

class IjroTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(32), default="new")  # new / done
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class EmployeeProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")

    full_name = db.Column(db.String(128))
    passport_info = db.Column(db.String(255))
    diploma_info = db.Column(db.String(255))
    other_docs = db.Column(db.String(255))

    passport_file = db.Column(db.String(255))
    diploma_file = db.Column(db.String(255))
    other_file = db.Column(db.String(255))
