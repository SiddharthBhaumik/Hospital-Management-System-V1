from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required,logout_user
from werkzeug.security import generate_password_hash
from datetime import date
from sqlalchemy.orm import aliased

doctor =Blueprint('doctor',__name__,url_prefix='/doctor' )
  
@doctor.route('/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        #appointments of blacklisted patients are cancelled
        appointments = (
    Appointment.query
        .join(Appointment.doctor)
        .join(Doctor.user)
        .filter(
            Appointment.status == 'booked',
            User.user_id == current_user.user_id
        )
        .all()
)
        PatientUser = aliased(User)  # for patient
        DoctorUser = aliased(User)   # for doctor

        patients = (
    Patient.query
    .join(Patient.user.of_type(PatientUser))         # Patient → User
    .join(Patient.appointments)                     # Appointment
    .join(Appointment.doctor)                        # Doctor
    .join(Doctor.user.of_type(DoctorUser))          # Doctor → User
    .filter(
        PatientUser.blacklisted == False,           # patient not blacklisted
        Appointment.status != "Cancelled",          # active appointments
        DoctorUser.user_id == current_user.user_id  # doctor is current user
    )
    .distinct()
    .all()
)

        return render_template('Doctor/doctor_dashboard.html',appointments=appointments,patients=patients)

@doctor.route('/change_login',methods=['GET','POST'])
@login_required
def doctor_edit_login_details():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        if request.method=='GET':
            return render_template("Doctor/doctor_change_login.html", user=current_user)
        elif request.method == "POST":
            new_username = request.form.get("username").strip()
            new_email = request.form.get("email").strip()
            new_password = request.form.get("password").strip()

            # ---- VALIDATION ----
            # Check if username exists (exclude current user)
            if User.query.filter(User.username == new_username,
                                User.user_id != current_user.user_id).first():
                flash("Username already taken. Please choose another.", "warning")
                return redirect(url_for("doctor.doctor_edit_login_details"))

            # Check if email exists
            if User.query.filter(User.email == new_email,
                                User.user_id != current_user.user_id).first():
                flash("Email already in use. Please choose another.", "warning")
                return redirect(url_for("doctor.doctor_edit_login_details"))


            current_user.username = new_username
            current_user.email = new_email

            if new_password:
                current_user.password = generate_password_hash(new_password)

            try:
                db.session.commit()

                # If login credentials changed significantly, force re-login
                if (new_username != current_user.username) or (new_email != current_user.email) or new_password:
                    flash("Login details updated. Please log in again.", "success")
                    logout_user()
                    return redirect(url_for("main.login"))

                return redirect(url_for("doctor.doctor_dashboard"))

            except Exception:
                db.session.rollback()
                flash("An error occurred while saving changes.", "danger")
                return redirect(url_for("doctor.edit_login_details"))

        # GET request → show form

@doctor.route('/treatment/<int:appointment_id>',methods=['GET','POST'])
@login_required
def doctor_treatment(appointment_id):
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        appt = (Appointment.query.join(Appointment.doctor).join(Doctor.user).filter( Appointment.appointment_id == appointment_id,
            User.user_id == current_user.user_id).first()
            )
        if not appt:
            flash("Appointment not found for doctor!", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))
        if appt.status=='cancelled':
                flash(f"This appointment is already cancelled.", "info")
                return redirect(url_for('doctor.doctor_dashboard'))
        
        treatment=Treatment.query.filter_by(appointment_id=appointment_id).first()
        
        if request.method=='GET':
            return render_template('Doctor/doctor_treatment.html',treatment=treatment,appointment=appt)
        elif request.method=='POST':    
            diagnosis = request.form.get('diagnosis').strip()
            prescription = request.form.get('prescription').strip()
            notes = request.form.get('notes', '').strip()
            tests = request.form.get('tests', '').strip()

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
                flash(f"Treatment saved successfully.", "success")
            except Exception as e:
                db.session.rollback()
                flash("An error occurred while saving treatment details.", "danger")

            return redirect(url_for('doctor.doctor_dashboard'))

    

@doctor.route('/update_appointment/<int:appointment_id>/<string:status>')
@login_required
def doctor_update_appointment_status(appointment_id,status):
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        appt = (Appointment.query.join(Appointment.doctor).join(Doctor.user).filter( Appointment.appointment_id == appointment_id,
            User.user_id == current_user.user_id).first()
            )
        if not appt:
            flash("Appointment not found for doctor!", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))
        
        if appt.status=='cancelled':
            flash(f"This appointment is already cancelled.", "info")
            return redirect(url_for('doctor.doctor_dashboard'))

        if status in ["completed", "cancelled"]:
            appt.status = status
        else:
            flash(f"Invalid Status.", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))
        try:
            db.session.commit()
            flash(f"Appointment has been successfully marked as {status}.", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the appointment status.", "danger")

        return redirect(url_for('doctor.doctor_dashboard'))


@doctor.route('/view_history/<int:patient_id>/<string:filter>')
@login_required
def doctor_patient_history(patient_id,filter):
    if current_user.role.role != 'Doctor':
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main.dashboard'))

    # Get patient
    patient = Patient.query.get(patient_id)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('doctor.doctor_dashboard'))

    today = date.today()
    patient_age= today.year - patient.dob.year - ((today.month, today.day) < (patient.dob.month, patient.dob.day))

    # Get filter from query string
    

    if filter == 'all':
        # Treatments from any doctor
        treatments = Treatment.query.join(Treatment.appointment).filter(
            Appointment.patient_id == patient.patient_id
        ).order_by(Appointment.datetime.desc()).all()
    elif filter == 'me':
        my_doctor = Doctor.query.filter_by(user_id=current_user.user_id).first()
        # Treatments only from this doctor
        treatments = Treatment.query.join(Treatment.appointment).filter(
        Appointment.patient_id == patient.patient_id,
        Appointment.doctor_id == my_doctor.doctor_id
    ).order_by(Appointment.datetime.desc()).all()
    else:
        flash("Invalid filter","danger")
        return redirect(url_for('doctor.doctor_dashboard'))

    return render_template('Doctor/patient_history.html',
                           patient=patient,
                           treatments=treatments,patient_age=patient_age)

@doctor.route('/availability',methods=['GET','POST'])
@login_required
def doctor_availability():
    if current_user.role.role != 'Doctor':
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main.dashboard'))
    
    doctor = Doctor.query.get(current_user.user_id)
    now = datetime.now()
    
    from datetime import datetime, timedelta
    if request.method=='GET':
        # Build slot list for next 7 days
        slots_by_date = {}
        doctor_availability_map = {}
        past_map = {}

        for i in range(7):
            day = datetime.today().date() + timedelta(days=i)

            slots = TimeSlot.query.order_by(TimeSlot.slot_start).all()
            slots_by_date[day] = slots

            for slot in slots:
                slot_datetime = datetime.combine(day, slot.slot_start)
                past_map[(day, slot.slot_id)] = (slot_datetime < now)

        for a in doctor.availabilities:
            doctor_availability_map[(a.date, a.slot_id)] = a
            return render_template("Doctor/doctor_availability.html",slots_by_date=slots_by_date,
        doctor_availability_map=doctor_availability_map,past_map=past_map)

    if request.method=='POST':
        raw_selected = request.form.getlist("selected_slots")
        selected = set()

        for item in raw_selected:
            date_str, slot_id = item.split("|")
            selected.add((date.fromisoformat(date_str), int(slot_id)))

        existing = {(a.date, a.slot_id): a for a in doctor.availabilities}
        preserved = {
            (a.date, a.slot_id)
            for a in doctor.availabilities
            if a.booked
        }
        final = selected.union(preserved)
        for key, availability in existing.items():
            if key not in preserved:
                db.session.delete(availability)


        for date_val, slot_id in final:
            if (date_val, slot_id) not in existing:
                db.session.add(DoctorAvailability(
                    doctor_id=doctor.doctor_id,
                    date=date_val,
                    slot_id=slot_id,
                    booked=False
                ))
        try:
            db.session.commit()
            flash(f"Availabilities have been saved.", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the availabilities.", "danger")
        return redirect(url_for("doctor.doctor_dashboard"))