from flask import Blueprint,render_template,request,redirect, url_for, flash,session
from flask_login import LoginManager,login_user,current_user,login_required,logout_user
from controller.models import *
from werkzeug.security import check_password_hash,generate_password_hash
from email_validator import validate_email, EmailNotValidError
import phonenumbers
import string
from datetime import datetime,date

main=Blueprint('main',__name__)

login_manager=LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/', methods=['GET'])
def home():
    return render_template('home.html') 

@main.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html',current_date=date.today().isoformat())

    elif request.method == 'POST': 
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '')
        dob_str = request.form.get('dob', '')
        phone_no = request.form.get('phone_no', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not all([name, gender, dob_str, phone_no, email, username, password]):
            flash("All fields are required.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        if not all(char.isalpha() or char.isspace() for char in name) or len(name) > 50:
            flash("Name can only contain letters and spaces and max 50 characters.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid gender selected.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            if dob > date.today():
                raise ValueError("DOB cannot be in the future")
        except ValueError:
            flash("Invalid date of birth.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        try:
            parsed_number = phonenumbers.parse(phone_no, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")
        except Exception:
            flash("Invalid phone number.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            flash("Invalid email address.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        if len(username) < 6 or len(username) > 20:
            flash("Username must be 6-20 characters long.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )
        if not username.isalnum():
            flash("Username can only contain letters and numbers.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )
        if not all(char.isalnum() or char in string.punctuation for char in password):
            flash("Password can only contain letters, numbers, or special characters.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )

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
        except Exception:
            db.session.rollback()
            flash("Error registering patient.", "danger")
            return render_template(
                'register.html',
                name=name, gender=gender, phone_no=phone_no,
                email=email, username=username, dob=dob_str,
                current_date=date.today().isoformat()
            )
        
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.role == 'Patient':
        return redirect(url_for('patient.patient_dashboard'))
    elif current_user.role.role == 'Doctor':
        return redirect(url_for('doctor.doctor_dashboard'))
    elif current_user.role.role == 'Admin':
        return redirect(url_for('admin.admin_dashboard'))

@main.route('/patient-login', methods=['GET', 'POST'])
def patient_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == 'GET':
        return render_template('patient_login.html')

    email = request.form.get('email', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not all([email, username, password]):
        flash("All fields are required.", "danger")
        return render_template('patient_login.html', email=email, username=username)

    try:
        valid_email = validate_email(email).email
    except EmailNotValidError:
        flash("Invalid email format.", "danger")
        return render_template('patient_login.html', email=email, username=username)

    if len(username) < 6 or len(username) > 20 or not username.isalnum():
        flash("Username must be 6–20 characters long and alphanumeric.", "danger")
        return render_template('patient_login.html', email=email, username=username)
    
    if len(password) < 8:
        flash("Password must be at least 8 characters long.", "danger")
        return render_template('patient_login.html', email=email, username=username)
    if not all(char.isalnum() or char in string.punctuation for char in password):
        flash("Password can only contain letters, numbers, or special characters.", "danger")
        return render_template('patient_login.html', email=email, username=username)

    user = User.query.filter((User.email == valid_email) & (User.username == username)).first()

    if user and check_password_hash(user.password, password) and user.role.role == 'Patient':
        if user.blacklisted:
            flash("Your account has been blacklisted.", "danger")
            return render_template('patient_login.html', email=email, username=username)

        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for('main.dashboard'))

    else:
        flash("Invalid credentials!", "danger")
        return render_template('patient_login.html', email=email, username=username)


@main.route('/staff-login', methods=['GET', 'POST'])
def staff_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == 'GET':
        return render_template('staff_login.html')

    role = request.form.get('role', '').strip()
    email = request.form.get('email', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not all([role, email, username, password]):
        flash("All fields are required.", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)

    if role not in ['Admin', 'Doctor']:
        flash("Invalid role selected.", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)

    try:
        valid_email = validate_email(email).email
    except EmailNotValidError:
        flash("Invalid email format.", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)
    
    if len(username) < 6 or len(username) > 20 or not username.isalnum():
        flash("Username must be 6–20 characters long and alphanumeric.", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)

    if len(password) < 8:
        flash("Password must be at least 8 characters long.", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)
    if not all(char.isalnum() or char in string.punctuation for char in password):
        flash("Password can only contain letters, numbers, or special characters.", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)

    user = User.query.filter((User.email == valid_email) & (User.username == username)).first()

    if user and check_password_hash(user.password, password) and user.role.role == role:
        if user.blacklisted:
            flash("Your account has been blacklisted.", "danger")
            return render_template('staff_login.html', email=email, username=username, role=role)

        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for('main.dashboard'))

    else:
        flash("Invalid credentials!", "danger")
        return render_template('staff_login.html', email=email, username=username, role=role)

        
@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear() 
    flash("Logged out successfully.")
    return redirect(url_for('main.home'))
    


