from flask import Blueprint,render_template,request,redirect, url_for, flash
from flask_login import LoginManager,login_user,current_user,login_required
from controller.models import *
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime

main=Blueprint('main',__name__)

login_manager=LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/', methods=['GET'])
def home():
    return render_template('home.html')

# REGISTER 

@main.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == 'POST': 
        name = request.form.get('name')    
        gender = request.form.get('gender') 
        dob_str = request.form.get('dob')
        phone_no = request.form.get('phone_no') 
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # ---- Parse DOB safely ----
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except:
            flash("Invalid Date of Birth!", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str
            )

        # ---- Email Exists Check ----
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash("Email already exists!", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, dob=dob_str,
                phone_no=phone_no, email=email, username=username
            )

        # ---- Username Exists Check ----
        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash("Username already exists!", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, dob=dob_str,
                phone_no=phone_no, email=email, username=username
            )

        # ---- Create New Patient & User ----
        patient_role = Roles.query.filter_by(role='Patient').first()

        patient_user = User(
            email=email,
            username=username,
            password=generate_password_hash(password),
            role=patient_role
        )

        patient = Patient(
            name=name,
            gender=gender,
            dob=dob,
            phone_no=phone_no,
            user=patient_user
        )

        try:
            db.session.add(patient)
            db.session.commit()
            flash("Patient registered successfully!", "success")
            return redirect(url_for('main.patient_login'))

        except Exception as e:
            db.session.rollback()
            flash("Error registering patient", "danger")
            return render_template('register.html')

        
# DASHBOARD
        
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.role == 'Patient':
        return render_template('Patient/patient_dashboard.html')
    elif current_user.role.role == 'Doctor':
        return redirect(url_for('doctor.doctor_dashboard'))
    elif current_user.role.role == 'Admin':
        return render_template('Admin/admin_dashboard.html')

@main.route('/patient_login',methods=['GET','POST'])
def patient_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method=='GET':
        return render_template('patient_login.html')
    if request.method=='POST':
        email= request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter((User.email == email) & (User.username == username)).first()

        if user and check_password_hash(user.password, password) and user.role.role=='Patient':
            if user.blacklisted:
                flash("Your Account has been blacklisted" , "danger")
                return render_template('staff_login.html')
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('main.dashboard'))  
        else:
            flash("Invalid credentials!", "danger")
            return render_template('patient_login.html')

@main.route('/staff_login',methods=['GET','POST'])
def staff_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method=='GET':
        return render_template('staff_login.html')
    elif request.method=='POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter((User.email == email) & (User.username == username)).first()

        if user and check_password_hash(user.password, password) and user.role.role==role:
            if user.blacklisted:
                flash("Your Account has been blacklisted" , "danger")
                return render_template('staff_login.html')
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('main.dashboard'))  
        else:
            flash("Invalid credentials!" , "danger")
            return render_template('staff_login.html')

    


