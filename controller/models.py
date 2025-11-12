from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db=SQLAlchemy()

class User(db.Model,UserMixin):
    __tablename__='user'
    user_id =db.Column(db.Integer,primary_key=True,autoincrement=True)
    email=db.Column(db.String(320),unique=True,nullable=False)
    username=db.Column(db.String(20),unique=True,nullable=False)
    password=db.Column(db.String(50),nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    role=db.relationship('Roles',back_populates='users',uselist=False)

class Roles(db.Model):
    __tablename__='roles'
    role_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    role = db.Column(db.String(20),unique=True,nullable=False)
    users = db.relationship('User', back_populates='role',uselist=True)

class Patient(db.Model):
    __tablename__='patient'
    patient_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    name=db.Column(db.String(50))
    gender=db.Column(db.String(10))
    phone_no=db.Column(db.String(15))

    user = db.relationship('User', uselist=False)


