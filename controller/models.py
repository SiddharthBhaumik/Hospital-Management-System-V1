from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db=SQLAlchemy()

class User(db.Model,UserMixin):
    __tablename__='user'
    user_id =db.Column(db.Integer,primary_key=True,autoincrement=True)
    email=db.Column(db.String(320),unique=True,nullable=False)
    username=db.Column(db.String(20),unique=True,nullable=False)
    password=db.Column(db.String(255),nullable=False)
    blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)

    role=db.relationship('Roles',back_populates='users',uselist=False)

    def get_id(self):
        return str(self.user_id)

class Roles(db.Model):
    __tablename__='roles'
    role_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    role = db.Column(db.String(20),unique=True,nullable=False)

    users = db.relationship('User', back_populates='role',uselist=True)

class Patient(db.Model):
    __tablename__='patient'
    patient_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    name=db.Column(db.String(50), nullable=False)
    gender=db.Column(db.String(10), nullable=False)
    phone_no=db.Column(db.String(15), nullable=False)

    user = db.relationship('User', uselist=False)
    appointments = db.relationship('Appointment', back_populates='patient',uselist=True)

class Doctor(db.Model):
    __tablename__='doctor'
    doctor_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=False)
    name=db.Column(db.String(50), nullable=False)
    experience=db.Column(db.Integer, nullable=False)
    about=db.Column(db.String(1000), nullable=False)

    user = db.relationship('User', uselist=False)
    availabilities = db.relationship('DoctorAvailability', back_populates='doctor',uselist=True)
    appointments = db.relationship('Appointment', back_populates='doctor',uselist=True)

class Department(db.Model):
    __tablename__='department'
    department_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.String(50), nullable=False,unique=True)
    description=db.Column(db.String(1000), nullable=False)

    doctors = db.relationship('Doctor', uselist=True)

class Appointment(db.Model):
    __tablename__='appointment'
    appointment_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    patient_id=db.Column(db.Integer, db.ForeignKey('patient.patient_id'), nullable=False)
    doctor_id=db.Column(db.Integer, db.ForeignKey('doctor.doctor_id'), nullable=False)
    status=db.Column(db.String(20), nullable=False)
    datetime=db.Column(db.DateTime,nullable=False)

    doctor = db.relationship('Doctor',back_populates='appointments', uselist=False)
    patient = db.relationship('Patient', back_populates='appointments',uselist=False)

class Treatment(db.Model):
    __tablename__='treatmentt'
    treatment_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    appointment_id=db.Column(db.Integer, db.ForeignKey('appointment.appointment_id'), nullable=False)
    diagnosis=db.Column(db.String(1000), nullable=False)
    prescription=db.Column(db.String(1000), nullable=False)
    notes=db.Column(db.String(1000), nullable=True)

    appointment = db.relationship('Appointment', uselist=False)

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    avail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.doctor_id'), nullable=False)
    available_datetime = db.Column(db.DateTime, nullable=False)

    doctor = db.relationship('Doctor', back_populates='availabilities',uselist=False)




