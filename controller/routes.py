from flask import Blueprint,render_template,request,flash,url_for,redirect
from werkzeug.security import generate_password_hash
from controller.models import *
from flask_login import current_user,login_required

main =Blueprint('main',__name__ )

@main.route('/', methods=['GET'])
def home():
    return render_template('home.html')

# REGISTER 

@main.route('/register', methods=['GET','POST'])
def register():
    if request.method=='GET':
        return render_template('register.html')
    elif request.method=='POST':      
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()

        print("Email:", email, "Username:", username, "Password:", password)
        print("Existing user:", existing_user)

        if existing_user:
            flash("Email or username already exists!", "danger")
            return render_template('register.html')
        
        patient_role = Roles.query.filter_by(role='Patient').first()
        patient_user = User(
            email=email,
            username=username,
            password=generate_password_hash(password),  
            role=patient_role
        )
        patient=Patient(
            user=patient_user
        )

        try:
            db.session.add(patient)
            db.session.commit()
            flash("Patient registered successfully!", "success")
            return redirect(url_for('auth.patient_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering patient: {str(e)}", "danger")
            return render_template('register.html')
        
# DASHBOARD
        
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.role == 'Patient':
        return render_template('Patient/patient_dashboard.html')
    elif current_user.role.role == 'Doctor':
        return render_template('Doctor/doctor_dashboard.html')
    elif current_user.role.role == 'Admin':
        return render_template('Admin/admin_dashboard.html')
    
        



