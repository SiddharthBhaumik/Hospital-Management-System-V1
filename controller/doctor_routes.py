from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required,logout_user
from werkzeug.security import generate_password_hash
from datetime import date
from sqlalchemy.orm import aliased
from email_validator import validate_email, EmailNotValidError
import string

doctor =Blueprint('doctor',__name__,url_prefix='/doctor' )
  
@doctor.route('/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        appointments = (Appointment.query.join(Appointment.doctor).join(Doctor.user)
        .filter(Appointment.status == 'booked',User.user_id == current_user.user_id).all())

        PatientUser = aliased(User)  
        DoctorUser = aliased(User)  

        patients = (Patient.query
                    .join(Patient.user.of_type(PatientUser))        
                    .join(Patient.appointments)                     
                    .join(Appointment.doctor)                        
                    .join(Doctor.user.of_type(DoctorUser))          
                    .filter(PatientUser.blacklisted == False,Appointment.status != "cancelled",DoctorUser.user_id == current_user.user_id  
                            ).distinct().all())

        return render_template('Doctor/doctor_dashboard.html',appointments=appointments,patients=patients)

@doctor.route('/edit-login-details', methods=['GET', 'POST'])
@login_required
def doctor_edit_login_details():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))

    if request.method == 'GET':
        return render_template("Doctor/doctor_change_login.html", user=current_user)

    elif request.method == 'POST':
        old_username = current_user.username
        old_email = current_user.email

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

        if len(username) < 6 or len(username) > 20:
            flash("Username must be 6-20 characters long.", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

        if not username.isalnum():
            flash("Username can only contain letters and numbers.", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            flash("Invalid email", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

        if User.query.filter(User.username == username, User.user_id != current_user.user_id).first():
            flash("Username already taken. Please choose another.", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

        if User.query.filter(User.email == email, User.user_id != current_user.user_id).first():
            flash("Email already in use. Please choose another.", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

        if password:
            if len(password) < 8:
                flash("Password must be at least 8 characters long.", "danger")
                return render_template("Doctor/doctor_change_login.html", user=current_user)
            if not all(char.isalnum() or char in string.punctuation for char in password):
                flash("Password can only contain letters, numbers, or special characters.", "danger")
                return render_template("Doctor/doctor_change_login.html", user=current_user)

        current_user.username = username
        current_user.email = email
        if password:
            current_user.password = generate_password_hash(password)

        try:
            db.session.commit()
            if password or username != old_username or email != old_email:
                return redirect(url_for("main.logout"))
            return redirect(url_for("doctor.doctor_dashboard"))
        except Exception:
            db.session.rollback()
            flash("An error occurred while saving changes.", "danger")
            return render_template("Doctor/doctor_change_login.html", user=current_user)

@doctor.route('/treatment/<int:appointment_id>',methods=['GET','POST'])
@login_required
def doctor_treatment(appointment_id):
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        appt = (Appointment.query.join(Appointment.doctor).join(Doctor.user).filter( Appointment.appointment_id == appointment_id,
            User.user_id == current_user.user_id).first())
        if not appt:
            flash("Appointment not found for doctor!", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))
        if appt.status=='cancelled':
            flash("This appointment is already cancelled.", "info")
            return redirect(url_for('doctor.doctor_dashboard'))
        
        treatment=Treatment.query.filter_by(appointment_id=appointment_id).first()
        
        if request.method=='GET':
            return render_template('Doctor/doctor_treatment.html',treatment=treatment,appointment=appt)
        elif request.method=='POST':    
            diagnosis = request.form.get('diagnosis').strip()
            prescription = request.form.get('prescription').strip()
            notes = request.form.get('notes', '').strip()
            tests = request.form.get('tests', '').strip()

            if not diagnosis:
                flash("Diagnosis is required.", "danger")
                return render_template('Doctor/doctor_treatment.html', treatment=treatment, appointment=appt)
            if not prescription:
                flash("Prescription is required.", "danger")
                return render_template('Doctor/doctor_treatment.html', treatment=treatment, appointment=appt)

            if treatment:
                treatment.diagnosis = diagnosis
                treatment.prescription = prescription
                treatment.notes = notes
                treatment.tests = tests
            else:
                treatment = Treatment(
                    appointment_id=appointment_id,
                    diagnosis=diagnosis,
                    prescription=prescription,
                    notes=notes,
                    tests=tests
                )
                db.session.add(treatment)
            try:
                db.session.commit()
                flash("Treatment saved successfully.", "success")
            except Exception:
                db.session.rollback()
                flash("An error occurred while saving treatment details.", "danger")

            return redirect(url_for('doctor.doctor_dashboard'))

@doctor.route('/update-appointment/<int:appointment_id>/<string:status>')
@login_required
def doctor_update_appointment_status(appointment_id,status):
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        appt = (Appointment.query.join(Appointment.doctor).join(Doctor.user).filter( Appointment.appointment_id == appointment_id,
            User.user_id == current_user.user_id).first())
        if not appt:
            flash("Appointment not found for doctor!", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))
        
        if appt.status=='cancelled':
            flash("This appointment is already cancelled.", "info")
            return redirect(url_for('doctor.doctor_dashboard'))

        if status in ["completed", "cancelled"]:
            if status == "completed":
                treatment = Treatment.query.filter_by(appointment_id=appt.appointment_id).first()
                if not treatment:
                    flash("Cannot mark appointment as completed because no treatment has been added.", "danger")
                    return redirect(url_for('doctor.doctor_dashboard'))

                appt.status = "completed"
            else:  
                appt.status = "cancelled"
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
        else:
            flash("Invalid Status.", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))
        try:
            db.session.commit()
            flash(f"Appointment has been successfully marked as {status}.", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the appointment status.", "danger")

        return redirect(url_for('doctor.doctor_dashboard'))

@doctor.route('/view-history/<int:patient_id>/<string:filter>')
@login_required
def doctor_patient_history(patient_id,filter):
    if current_user.role.role != 'Doctor':
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main.dashboard'))

    patient = Patient.query.get(patient_id)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('doctor.doctor_dashboard'))
    if not Appointment.query.join(Appointment.doctor).filter(Appointment.patient_id == patient.patient_id,
                                                             Doctor.user_id == current_user.user_id).first():
        flash("You are not authorized to view this patient.", "danger")
        return redirect(url_for('doctor.doctor_dashboard'))

    today = date.today()
    patient_age= today.year - patient.dob.year - ((today.month, today.day) < (patient.dob.month, patient.dob.day))
  
    if filter == 'all':
        treatments = Treatment.query.join(Treatment.appointment).filter(
            Appointment.patient_id == patient.patient_id).order_by(Appointment.datetime.desc()).all()
    elif filter == 'me':
        doctor_id = db.session.query(Doctor.doctor_id).filter_by(user_id=current_user.user_id).scalar()
        treatments = Treatment.query.join(Treatment.appointment).filter(
            Appointment.patient_id == patient.patient_id,Appointment.doctor_id ==doctor_id).order_by(
                Appointment.datetime.desc()).all()
    else:
        flash("Invalid filter","danger")
        return redirect(url_for('doctor.doctor_dashboard'))

    return render_template('Doctor/doctor_patient_history.html',patient=patient,treatments=treatments,patient_age=patient_age)

@doctor.route('/availability', methods=['GET', 'POST'])
@login_required
def doctor_availability():
    if current_user.role.role != 'Doctor':
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main.dashboard'))

    doctor = Doctor.query.filter_by(user_id=current_user.user_id).first()

    from datetime import datetime, timedelta
    now = datetime.now()

    if request.method == 'GET':
        slots_by_date = {}
        doctor_availability_map = {}
        past_map = {}

        for i in range(7):
            day = date.today() + timedelta(days=i)

            slots = TimeSlot.query.order_by(TimeSlot.slot_start).all()
            slots_by_date[day] = slots

            for slot in slots:
                slot_datetime = datetime.combine(day, slot.slot_start)
                past_map[(day, slot.slot_id)] = (slot_datetime < now)

        for a in doctor.availabilities:
            doctor_availability_map[(a.date, a.slot_id)] = a

        return render_template(
            "Doctor/doctor_availability.html",
            slots_by_date=slots_by_date,
            doctor_availability_map=doctor_availability_map,
            past_map=past_map
        )

    if request.method == 'POST':

        raw_selected = request.form.getlist("selected_slots")
        selected = set()

        valid_dates = {date.today() + timedelta(days=i) for i in range(7)}
        valid_slot_ids = {s.slot_id for s in TimeSlot.query.all()}

        for item in raw_selected:
            if "|" not in item:
                flash("Invalid slot format.", "danger")
                return redirect(url_for("doctor.doctor_availability"))

            date_str, slot_id_str = item.split("|")

            try:
                date_val = date.fromisoformat(date_str)
            except ValueError:
                flash("Invalid date received.", "danger")
                return redirect(url_for("doctor.doctor_availability"))

            if date_val not in valid_dates:
                flash("Selected date is outside allowed range.", "danger")
                return redirect(url_for("doctor.doctor_availability"))
            
            try:
                slot_id = int(slot_id_str)
            except ValueError:
                flash("Invalid slot ID format.", "danger")
                return redirect(url_for("doctor.doctor_availability"))

            if slot_id not in valid_slot_ids:
                flash("Selected slot is invalid.", "danger")
                return redirect(url_for("doctor.doctor_availability"))

            slot_time = TimeSlot.query.get(slot_id).slot_start
            slot_datetime = datetime.combine(date_val, slot_time)

            if slot_datetime < now:
                flash("Cannot select slots in the past.", "danger")
                return redirect(url_for("doctor.doctor_availability"))

            selected.add((date_val, slot_id))

        existing = {(a.date, a.slot_id): a for a in doctor.availabilities}

        preserved = {
            (a.date, a.slot_id)
            for a in doctor.availabilities
            if a.booked
        }

        for key, availability in existing.items():
            if key not in preserved and key not in selected:
                db.session.delete(availability)

        for date_val, slot_id in selected:
            if (date_val, slot_id) not in existing:
                db.session.add(
                    DoctorAvailability(
                        doctor_id=doctor.doctor_id,
                        date=date_val,
                        slot_id=slot_id,
                        booked=False
                    )
                )
        try:
            db.session.commit()
            flash("Availabilities have been saved.", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating availabilities.", "danger")

        return redirect(url_for("doctor.doctor_dashboard"))
