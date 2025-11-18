from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required
from sqlalchemy.orm import aliased

doctor =Blueprint('doctor',__name__ )
  
@doctor.route('/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        # appointments of blacklisted patients are cancelled
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
        patients = Patient.query.filter(
            Patient.user.has(User.blacklisted == False),
            Patient.appointments.any(
                Appointment.status != "Cancelled",
                Appointment.doctor.has(
                    Doctor.user.has(User.user_id == current_user.user_id)
                )
            )
        ).all()

        return render_template('Doctor/doctor_dashboard.html',appointments=appointments,patients=patients)

@doctor.route('/change_login',methods=['GET','POST'])
@login_required
def doctor_edit_login_details():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:

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


@doctor.route('/view_history/<int:patient_id>')
@login_required
def doctor_patient_history(patient_id):
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        patient=Patient.query.get(patient_id)
        if not patient:
            flash("Appointment not found for doctor!", "danger")
            return redirect(url_for('doctor.doctor_dashboard'))