from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required,logout_user
from werkzeug.security import generate_password_hash
from email_validator import validate_email, EmailNotValidError
from datetime import datetime,date
import phonenumbers
import string

patient =Blueprint('patient',__name__ ,url_prefix='/patient')

@patient.route('/dashboard')
@login_required
def patient_dashboard():
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        departments=Department.query.all()
        appointments = Appointment.query.join(Appointment.patient
                                              ).filter( Patient.user_id == current_user.user_id,Appointment.status == 'booked').all()

        return render_template('Patient/patient_dashboard.html',appointments=appointments,departments=departments)
    
@patient.route('/edit-login-details', methods=['GET', 'POST'])
@login_required
def patient_edit_login_details():
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        if request.method == 'GET':
            return render_template("Patient/patient_change_login.html", user=current_user)
        if request.method == 'POST':
            old_username = current_user.username
            old_email = current_user.email

            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not username or not email:
                flash("Username and email are required.", "danger")
                return render_template("Patient/patient_change_login.html", user=current_user)

            if len(username) < 6 or len(username) > 20:
                flash("Username must be 6-20 characters long.", "danger")
                return render_template("Patient/patient_change_login.html", user=current_user)

            if not username.isalnum():
                flash("Username can only contain letters and numbers.", "danger")
                return render_template("Patient/patient_change_login.html", user=current_user)

            try:
                valid = validate_email(email)
                email = valid.email
            except EmailNotValidError:
                flash("Invalid email", "danger")
                return render_template("Patient/patient_change_login.html", user=current_user)

            if User.query.filter(User.username == username, User.user_id != current_user.user_id).first():
                flash("Username already taken. Please choose another.", "danger")
                return render_template("Patient/patient_change_login.html", user=current_user)

            if User.query.filter(User.email == email, User.user_id != current_user.user_id).first():
                flash("Email already in use. Please choose another.", "danger")
                return render_template("Patient/patient_change_login.html", user=current_user)
            
            if password:
                if len(password) < 8:
                    flash("Password must be at least 8 characters long.", "danger")
                    return render_template("Patient/patient_change_login.html", user=current_user)
                if not all(char.isalnum() or char in string.punctuation for char in password):
                    flash("Password can only contain letters, numbers, or special characters.", "danger")
                    return render_template("Patient/patient_change_login.html", user=current_user)

            current_user.username = username
            current_user.email = email
            if password:
                current_user.password = generate_password_hash(password)
            try:
                db.session.commit()
                if password or username != old_username or email != old_email:
                    return redirect(url_for("main.logout"))
                return redirect(url_for("patient.patient_dashboard"))
            except Exception:
                db.session.rollback()
                flash("An error occurred while saving changes.", "danger")
                return redirect(url_for("patient.patient_edit_login_details"))
            
@patient.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def patient_edit_profile():
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        patient = Patient.query.filter_by(user_id=current_user.user_id).first()
        if request.method == 'GET':
            return render_template("Patient/patient_edit_profile.html",patient=patient)
        if request.method == 'POST':
            name = request.form.get("name", "").strip()
            gender = request.form.get("gender", "")
            dob_str = request.form.get("dob", "")
            phone_no = request.form.get("phone_no", "").strip()

            if not all([name, gender, phone_no, dob_str]):
                flash("All required fields must be filled!", "danger")
                return render_template("Patient/patient_edit_profile.html",patient=patient)
            
            if not all(char.isalpha() or char.isspace() for char in name) or len(name) > 50:
                flash("Name can only contain letters and spaces and must not exceed 50 characters.", "danger")
                return render_template("Patient/patient_edit_profile.html",patient=patient)

            if gender not in ['Male', 'Female', 'Other']:
                flash("Invalid gender selected.", "danger")
                return render_template("Patient/patient_edit_profile.html",patient=patient)
    
            try:
                parsed_number = phonenumbers.parse(phone_no, None)
                if not phonenumbers.is_valid_number(parsed_number):
                    raise ValueError("Invalid phone number")
            except Exception:
                flash("Invalid phone number.", "danger")
                return render_template("Patient/patient_edit_profile.html",patient=patient)

            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                if dob > date.today():
                    raise ValueError("DOB cannot be in the future")
            except Exception:
                flash("Invalid date of birth.", "danger")
                return render_template("Patient/patient_edit_profile.html",patient=patient)
            patient.name = name
            patient.gender = gender
            patient.dob = dob
            patient.phone_no = phone_no

            try:
                db.session.commit()
                flash("Profile updated successfully.", "success")
                return redirect(url_for('patient.patient_dashboard'))
            except Exception:
                db.session.rollback()
                flash("An error occurred while saving changes.", "danger")
                return redirect(url_for('patient.patient_edit_profile'))

@patient.route('/department/<int:dept_id>')
@login_required
def patient_view_department(dept_id):
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        department = Department.query.get(dept_id)
        if not department:
            flash("Department not found.", "danger")
            return redirect(url_for("patient.patient_dashboard"))
        doctors = Doctor.query.join(Doctor.user).filter(
            Doctor.department_id == department.department_id,User.blacklisted == False).all()

        return render_template("Patient/patient_deptdoc.html",department=department,doctors=doctors)

@patient.route('/cancel-appointment/<int:appt_id>', methods=['POST'])
@login_required
def patient_cancel_appointment(appt_id):
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        appointment = Appointment.query.get(appt_id)
        if not appointment:
            flash("Appointment not found.", "danger")
            return redirect(url_for('patient.patient_dashboard'))

        appt = (Appointment.query.join(Appointment.patient).join(Patient.user).filter( Appointment.appointment_id == appt_id,
            User.user_id == current_user.user_id).first()
            )
        if not appt:
            flash("Appointment not found for patient!", "danger")
            return redirect(url_for('patient.patient_dashboard'))

        if appointment.status == 'completed':
            flash("Cannot cancel a completed appointment.", "warning")
            return redirect(url_for('patient.patient_dashboard'))

        appointment.status = 'cancelled'
        appt_date = appt.datetime.date()
        appt_time = appt.datetime.time()
        slot = TimeSlot.query.filter_by(slot_start=appt_time).first()
        if slot:
            availability = DoctorAvailability.query.filter_by(
                        doctor_id=appt.doctor_id,
                        date=appt_date,
                        slot_id=slot.slot_id
                    ).first()
            if availability:
                availability.booked = False
        try:
            db.session.commit()
            flash("Appointment cancelled successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while cancelling the appointment.", "danger")

        return redirect(url_for('patient.patient_dashboard'))

@patient.route('/treatment-history')
@login_required
def patient_history():
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        patient = Patient.query.filter_by(user_id=current_user.user_id).first()

        treatments = Treatment.query.join(Treatment.appointment).join(
            Appointment.doctor).join(Doctor.department).filter(Appointment.patient_id == patient.patient_id).order_by(
                Appointment.datetime.desc()).all()

        return render_template("Patient/patient_history.html",patient=patient,treatments=treatments)
    
@patient.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def patient_book_appointment(doctor_id):
    if current_user.role.role != "Patient":
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for("main.dashboard"))
    
    patient = Patient.query.filter_by(user_id=current_user.user_id).first()
    doctor = Doctor.query.join(Doctor.user).filter(User.blacklisted==False,Doctor.doctor_id==doctor_id).first()
    if not doctor:
        flash("Doctor not found!", "danger")
        return redirect(url_for('patient.patient_dashboard'))
    
    now = datetime.now()
    if request.method == "GET":
        availabilities = (
            DoctorAvailability.query
            .filter_by(doctor_id=doctor_id, booked=False)
            .join(TimeSlot)
            .filter((DoctorAvailability.date > now.date()) | ((DoctorAvailability.date == now.date()) & (TimeSlot.slot_start > now.time())))
            .order_by(DoctorAvailability.date, TimeSlot.slot_start).all())

        return render_template(
            "Patient/patient_book.html",
            doctor=doctor,
            availabilities=availabilities
        )

    if request.method == "POST":
        availability_id = request.form.get("availability_id")
        availability = DoctorAvailability.query.get_or_404(availability_id)

        if availability.doctor_id != doctor_id:
            flash("Invalid appointment slot.", "danger")
            return redirect(url_for('patient.patient_book_appointment'))

        if availability.booked:
            flash("This slot has already been booked.", "danger")
            return redirect(url_for('patient.patient_book_appointment'))

        slot_datetime = datetime.combine(
            availability.date,
            availability.time_slot.slot_start
        )

        if slot_datetime <= now:
            flash("Cannot book a slot in the past.", "danger")
            return redirect(url_for('patient.patient_book_appointment'))
        
        conflict = (
            Appointment.query
            .filter_by(patient_id=patient.patient_id)
            .filter(Appointment.datetime == slot_datetime)
            .first()
        )

        if conflict:
            flash("You already have another appointment at the same time!", "danger")
            return redirect(url_for('patient.patient_book_appointment'))

        try:
            availability.booked = True

            new_appointment = Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                datetime=slot_datetime,
                status="booked"
            )

            db.session.add(new_appointment)
            db.session.commit()

            flash("Appointment booked successfully!", "success")
            return redirect(url_for("patient.patient_dashboard"))

        except Exception:
            db.session.rollback()
            flash("An error occurred while booking appointment.", "danger")
            return redirect(url_for('patient.patient_book_appointment'))




