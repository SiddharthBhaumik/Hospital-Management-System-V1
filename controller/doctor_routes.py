from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required

doctor =Blueprint('doctor',__name__ )
  
@doctor.route('/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.role != 'Doctor':
        return redirect(url_for('main.dashboard'))
    else:
        appointments =Appointment.query.join(Appointment.doctor).join(Doctor.user).join(Appointment.patient).join(Patient.user).filter(
            Appointment.status == 'Booked',User.user_id == current_user.user_id,Patient.user.has(blacklisted=False)).all()

        patients=Patient.query.join(Patient.user).filter

        return render_template('Doctor/doctor_dashboard.html',appointments=appointments,patients=patients)



@doctor.route('/doctors')
@login_required
def patient_history():