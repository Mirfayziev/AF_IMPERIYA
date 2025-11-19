from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ---------------- USER MODEL ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="employee")  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


# ---------------- EMPLOYEE PROFILE ---------------- #

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


# ---------------- VEHICLE MODEL ---------------- #

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))  
    number_plate = db.Column(db.String(32))
    driver_name = db.Column(db.String(128))
    monthly_limit = db.Column(db.Float)
    last_repair = db.Column(db.Date)
    status = db.Column(db.String(64))
    
    image_file = db.Column(db.String(255))

    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    organization = db.relationship("Organization")

    def __repr__(self):
        return f"<Vehicle {self.number_plate}>"


# ---------------- ORGANIZATION ---------------- #

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    address = db.Column(db.String(255))
    floor = db.Column(db.String(32))
    employee_count = db.Column(db.Integer)

    vehicles = db.relationship("Vehicle", backref="org", lazy=True)


# ---------------- OUTSOURCE COMPANY ---------------- #

class OutsourceCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    service_type = db.Column(db.String(128))
    contract_number = db.Column(db.String(64))
    contract_date = db.Column(db.Date)
    contract_amount = db.Column(db.Float)
    comment = db.Column(db.Text)


# ---------------- ORGTECH ---------------- #

class OrgTech(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    model = db.Column(db.String(128))
    serial_number = db.Column(db.String(128))
    status = db.Column(db.String(64))  
    last_update = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User")


# ---------------- CONTRACT MODEL ---------------- #

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    contract_number = db.Column(db.String(64))
    date = db.Column(db.Date)
    amount = db.Column(db.Float)

    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    organization = db.relationship("Organization")


# ---------------- IJRO TASKS ---------------- #

class IjroTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(32), default="pending")

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))


# ---------------- SOLAR DATA ---------------- #

class SolarSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(128))
    location = db.Column(db.String(255))


class SolarReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("solar_site.id"))
    site = db.relationship("SolarSite")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    energy_generated = db.Column(db.Float)
