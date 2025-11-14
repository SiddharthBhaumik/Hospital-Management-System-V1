from controller.routes import main,login_manager
from controller.admin_routes import admin
from controller.config import config
from controller.models import Roles,User,db
from werkzeug.security import generate_password_hash
from flask import Flask

# INIT

app =Flask(__name__ , template_folder='templates',static_folder='static')
app.register_blueprint(main)
app.register_blueprint(admin)
login_manager.init_app(app)
app.config.from_object(config)
db.init_app(app)

login_manager.login_view='main.home'

# DATABASE CREATION

with app.app_context():
    db.create_all()

    admin_role= Roles.query.filter_by(role='Admin').first()
    if not admin_role:
        admin_role=Roles(role='Admin')
        db.session.add(admin_role)
    
    doctor_role= Roles.query.filter_by(role='Doctor').first()
    if not doctor_role:
        doctor_role=Roles(role='Doctor')
        db.session.add(doctor_role)

    patient_role= Roles.query.filter_by(role='Patient').first()
    if not patient_role:
        patient_role=Roles(role='Patient')
        db.session.add(patient_role)

    admin_user=User.query.filter_by(email='admin@gmail.com').first()
    if not admin_user:
        admin_user=User(email='admin@gmail.com',username='admin',password=generate_password_hash('1234567890'),role=admin_role)
        db.session.add(admin_user)

    db.session.commit()



if __name__ =="__main__":
    app.run(debug=True)
