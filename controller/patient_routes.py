from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required,logout_user
from werkzeug.security import generate_password_hash
from datetime import datetime

patient =Blueprint('patient',__name__ ,url_prefix='/patient')

@patient.route('/dashboard')
@login_required
def patient_dashboard():
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        departments=Department.query.all()
        appointments = Appointment.query.join(Appointment.patient).filter( 
    Patient.user_id == current_user.user_id,
    Appointment.status == 'booked'
).all()

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
            username = request.form.get('username').strip()
            email = request.form.get('email').strip()
            password = request.form.get('password').strip()

            # --- Check if username exists (but not for this user)
            existing_username = User.query.filter(
                User.username == username,
                User.user_id != current_user.user_id
            ).first()

            if existing_username:
                flash("Username is already taken.", "danger")
                return redirect(url_for('patient.patient_edit_login_details'))

            # --- Check if email exists (but not for this user)
            existing_email = User.query.filter(
                User.email == email,
                User.user_id != current_user.user_id
            ).first()

            if existing_email:
                flash("Email is already registered.", "danger")
                return redirect(url_for('patient.patient_edit_login_details'))

            # --- Update fields
            current_user.username = username
            current_user.email = email

            # Update password only if given
            if password:
                current_user.password = generate_password_hash(password)
                flash("Password updated successfully.", "success")
            try:
                db.session.commit()

                # If login credentials changed significantly, force re-login
                if (username != current_user.username) or (email != current_user.email) or password:
                    flash("Login details updated. Please log in again.", "success")
                    logout_user()
                    return redirect(url_for("main.login"))

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
    # Load the patient linked to this user
        patient = Patient.query.filter_by(user_id=current_user.user_id).first()
        if request.method == 'GET':
             return render_template(
            "Patient/edit_profile.html",
            patient=patient
        )
        if request.method == 'POST':
            name = request.form.get('name').strip()
            gender = request.form.get('gender')
            dob_str = request.form.get('dob')
            phone_no = request.form.get('phone_no').strip()

            # --- Validate date ---
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid date format.", "danger")
                return redirect(url_for('patient.patient_edit_profile'))

            # --- Update fields ---
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
        # Get the requested department
        department = Department.query.get(dept_id)
        if not department:
            flash("Department not found.", "danger")
            return redirect(url_for("patient.patient_dashboard"))
        doctors = Doctor.query.join(Doctor.user).filter(
        Doctor.department_id == department.department_id,
        User.blacklisted == False
        ).all()

        return render_template(
            "Patient/patient_deptdoc.html",
            department=department,
            doctors=doctors
        )

@patient.route('/cancel-appointment/<int:appt_id>', methods=['POST'])
@login_required
def patient_cancel_appointment(appt_id):
    if current_user.role.role != 'Patient':
        return redirect(url_for('main.dashboard'))
    else:
        # Get the appointment
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

        # Only cancel if not already completed/cancelled
        if appointment.status == 'completed':
            flash("Cannot cancel a completed appointment.", "warning")
            return redirect(url_for('patient.patient_dashboard'))

        appointment.status = 'cancelled'
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
        # Get the patient linked to the logged-in user
        patient = Patient.query.filter_by(user_id=current_user.user_id).first()

        # Load treatments with related appointment, doctor, department
        treatments = Treatment.query.join(Treatment.appointment)\
            .join(Appointment.doctor)\
            .join(Doctor.department)\
            .filter(Appointment.patient_id == patient.patient_id)\
            .order_by(Appointment.datetime.desc())\
            .all()

        return render_template(
            "Patient/patient_history.html",
            patient=patient,
            treatments=treatments
        )
    
@patient.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def patient_book_appointment(doctor_id):
    if current_user.role.role != "Patient":
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for("main.dashboard"))
    
    patient = Patient.query.filter_by(user_id=current_user.user_id).first()
    doctor = Doctor.query.join(Doctor.user).filter(User.blacklisted==False,Doctor.doctor_id==doctor_id)
    if not doctor:
        flash("Doctor not found!", "danger")
        return redirect(url_for('patient.patient_dashboard'))
    
    now = datetime.now()
    if request.method == "GET":
        availabilities = (
            DoctorAvailability.query
            .filter_by(doctor_id=doctor_id, booked=False)
            .join(TimeSlot)
            .filter((DoctorAvailability.date > now.date()) | (DoctorAvailability.date == now.date()) & (TimeSlot.slot_start > now.time()))
            .order_by(DoctorAvailability.date, TimeSlot.slot_start).all())

        return render_template(
            "Patient/book_appointment.html",
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
            return redirect(request.url)




