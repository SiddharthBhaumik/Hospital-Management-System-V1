from flask import Blueprint,render_template,request,flash,url_for,redirect
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from controller.models import *
from flask_login import current_user,login_required
from email_validator import validate_email, EmailNotValidError
from datetime import datetime,date,timedelta
import phonenumbers
import string


admin =Blueprint('admin',__name__ ,url_prefix='/admin')

@admin.route("/dashboard")
def admin_dashboard():
    total_departments = Department.query.count()
    
    active_doctors = db.session.query(Doctor).join(User).filter(
        User.blacklisted == False
    ).count()
    
    active_patients = db.session.query(Patient).join(User).filter(
        User.blacklisted == False
    ).count()
    
    doctors_per_dept = db.session.query(
        Department.name,
        func.count(Doctor.doctor_id)
    ).join(Doctor).group_by(Department.department_id).all()
    
    dept_labels = [dept[0] for dept in doctors_per_dept]
    doctors_counts = [dept[1] for dept in doctors_per_dept]
    
    completed_per_dept = db.session.query(
        Department.name,
        func.count(Appointment.appointment_id)
    ).join(Doctor).join(Appointment).filter(
        Appointment.status == 'completed'
    ).group_by(Department.department_id).all()
    
    completed_counts = [dept[1] for dept in completed_per_dept]
    
    today = datetime.now().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    
    last_7_completed = []
    for day in last_7_days:
        count = Appointment.query.filter(
            func.date(Appointment.datetime) == day,
            Appointment.status == 'completed'
        ).count()
        last_7_completed.append(count)
    
    last_7_labels = [day.strftime('%m/%d') for day in last_7_days]
    
    next_7_days = [(today + timedelta(days=i)) for i in range(7)]
    
    next_7_upcoming = []
    for day in next_7_days:
        count = Appointment.query.filter(
            func.date(Appointment.datetime) == day,
            Appointment.status == 'booked'
        ).count()
        next_7_upcoming.append(count)
    
    next_7_labels = [day.strftime('%m/%d') for day in next_7_days]
    
    chart_data = {
        'deptLabels': dept_labels,
        'doctorsPerDept': doctors_counts,
        'completedPerDept': completed_counts,
        'last7Labels': last_7_labels,
        'last7Completed': last_7_completed,
        'next7Labels': next_7_labels,
        'next7Upcoming': next_7_upcoming
    }
    
    return render_template(
        'admin/dashboard.html',
        total_departments=total_departments,
        active_doctors=active_doctors,
        active_patients=active_patients,
        chart_data=chart_data
    )
  
@admin.route('/doctors')
@login_required
def admin_doctors():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        search_by = request.args.get('search_by', 'name') 
        query = request.args.get('query', '').strip()

        doctors = Doctor.query

        if query:
            if search_by == 'name':
                doctors = doctors.filter(Doctor.name.ilike(f"%{query}%"))
            elif search_by == 'department':
                doctors = doctors.join(Doctor.department).filter(Department.name.ilike(f"%{query}%"))

        doctors = doctors.all()

        return render_template(
            'Admin/admin_doctors.html',
            doctors=doctors,
            search_by=search_by,
            query=query
        )

    
@admin.route('/add-doctor',methods=['GET','POST'])
@login_required
def admin_create_doctor():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        departments=Department.query.all()
        if request.method=='GET':
            return render_template('Admin/admin_doctor_create.html',departments=departments)
        elif request.method=='POST':
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')  
            name = request.form.get('name', '').strip()
            department_id = request.form.get('department_id', '').strip()
            experience = request.form.get('experience', '').strip()
            about = request.form.get('about', '').strip()


            if not all([email, username, password, name, department_id, experience]):
                flash("All required fields must be filled!", "danger")
                return render_template('Admin/admin_doctor_create.html',departments=departments, name=name, experience=experience, about=about, email=email, username=username,department_id=department_id)

            try:
                valid = validate_email(email)
                email = valid.email 
            except EmailNotValidError as e:
                flash(f"Invalid email: {str(e)}", "danger")
                return render_template('Admin/admin_doctor_create.html',departments=departments, name=name, experience=experience, about=about, email=email, username=username,department_id=department_id)

            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash("Email already exists!", "danger")
                return render_template('Admin/admin_doctor_create.html',departments=departments, name=name, experience=experience, about=about, email=email, username=username,department_id=department_id)

            username_exists = User.query.filter_by(username=username).first()
            if username_exists:
                flash("Username already exists!", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)
            if len(username) < 6 or len(username) > 20:
                flash("Username must be 6–20 characters long.", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)

            if not username.isalnum():
                flash("Username can only contain letters and numbers.", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)
            
            department = Department.query.get(department_id)
            if not department:
                flash("Selected department does not exist!", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)
            if len(about) > 500:
                flash("About section cannot exceed 500 characters.", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)
            
            if experience.isdigit():
                flash("Experience must be a positive integer.", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)
            
            if not all(char.isalnum() or char in string.punctuation for char in password) or len(password) < 8:
                flash("Password can only contain letters, numbers, or special characters and must be minimum 8 characters", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)
            
            if not all(char.isalpha() or char.isspace() for char in name) or len(name)>50:
                flash("Name can contain only letters and spaces and cannot exceed 50 characters", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, 
                                       experience=experience, about=about, email=email, username=username,department_id=department_id)

            
            doctor_role = Roles.query.filter_by(role='Doctor').first()
            doctor_user = User(
                email=email,
                username=username,
                password=generate_password_hash(password),  
                role=doctor_role)
            doctor=Doctor(name=name, experience=experience, department_id=department_id,about=about,user=doctor_user)

            try:
                db.session.add(doctor)
                db.session.commit()
                flash("Doctor added successfully!", "success")
                return redirect(url_for('admin.admin_doctors'))
            except Exception:
                db.session.rollback()
                flash(f"Error adding doctor", "danger")
                return render_template('Admin/admin_doctor_create.html',departments=departments)
            
@admin.route('/edit-doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def admin_doctors_edit(doctor_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        flash("Doctor not found!", "danger")
        return redirect(url_for('admin.admin_doctors'))

    departments = Department.query.all()

    if request.method == 'GET':
        return render_template('Admin/admin_doctor_edit.html', doctor=doctor, departments=departments)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department_id = request.form.get('department_id', '').strip()
        experience = request.form.get('experience', '').strip()
        about = request.form.get('about', '').strip()

        if not all([name, department_id, experience]):
            flash("All required fields must be filled!", "danger")
            return render_template('Admin/admin_doctor_edit.html', doctor=doctor, departments=departments)
        if not all(char.isalpha() or char.isspace() for char in name) or len(name) > 50:
            flash("Name can contain only letters and spaces and cannot exceed 50 characters", "danger")
            return render_template('Admin/admin_doctor_edit.html', doctor=doctor, departments=departments)

        if not experience.isdigit():
            flash("Experience must be a positive integer.", "danger")
            return render_template('Admin/admin_doctor_edit.html', doctor=doctor, departments=departments)

        if len(about) > 500:
            flash("About section cannot exceed 500 characters.", "danger")
            return render_template('Admin/admin_doctor_edit.html', doctor=doctor, departments=departments)

        department = Department.query.get(department_id)
        if not department:
            flash("Selected department does not exist!", "danger")
            return render_template('Admin/admin_doctor_edit.html', doctor=doctor, departments=departments)
        
        doctor.name = name
        doctor.department_id = department_id
        doctor.experience = experience
        doctor.about = about

        try:
            db.session.commit()
            flash("Doctor updated successfully!", "success")
        except Exception:
            db.session.rollback()
            flash("Error updating doctor", "danger")

        return redirect(url_for('admin.admin_doctors'))

@admin.route('/blacklist-doctor/<int:doctor_id>')
@login_required
def admin_doctors_blacklist(doctor_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        doctor=Doctor.query.get(doctor_id)
        if not doctor:
            flash("Doctor not found!", "danger")
            return redirect(url_for('admin.admin_doctors'))
        user=doctor.user
        
        user.blacklisted=not user.blacklisted
        if user.blacklisted:
            blacklisted_appts = (
            Appointment.query
            .filter(
                Appointment.doctor_id == doctor.doctor_id, 
                Appointment.status != "cancelled",
                )
            ).all()
            for appt in blacklisted_appts:
                appt.status = "cancelled"

        try:
            db.session.commit()
            status = "blacklisted" if user.blacklisted else "removed from blacklist"
            flash(f"Doctor has been successfully {status}.", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the blacklist status.", "danger")

        return redirect(url_for('admin.admin_doctors'))

@admin.route('/departments')
@login_required    
def admin_departments():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        departments=Department.query.all()
        return render_template('Admin/admin_department.html',departments=departments)

@admin.route('/add-department', methods=['GET', 'POST'])
@login_required
def admin_create_department():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))

    if request.method == 'GET':
        return render_template('Admin/admin_dept_create.html')
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name or not description:
            flash("Both department name and description are required!", "danger")
            return render_template('Admin/admin_dept_create.html', name=name, description=description)

        if not all(char.isalpha() or char.isspace() for char in name) or len(name) > 50:
            flash("Department name can contain only letters and spaces and cannot exceed 50 characters.", "danger")
            return render_template('Admin/admin_dept_create.html', name=name, description=description)

        existing_dept = Department.query.filter_by(name=name).first()
        if existing_dept:
            flash("Department already exists", "danger")
            return render_template('Admin/admin_dept_create.html', name=name, description=description)

        dept = Department(name=name, description=description)
        try:
            db.session.add(dept)
            db.session.commit()
            flash("Department added successfully!", "success")
            return redirect(url_for('admin.admin_departments'))
        except Exception:
            db.session.rollback()
            flash("An unexpected error occurred while adding the department.", "danger")
            return render_template('Admin/admin_dept_create.html', name=name, description=description)


@admin.route('/edit-department/<int:department_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_department(department_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))

    dept = Department.query.get(department_id)
    if not dept:
        flash("Department not found!", "danger")
        return redirect(url_for('admin.admin_departments'))

    if request.method == 'GET':
        return render_template('Admin/admin_dept_edit.html', dept=dept)
    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name or not description:
            flash("Both department name and description are required!", "danger")
            return render_template('Admin/admin_dept_edit.html', dept=dept)

        if not all(char.isalpha() or char.isspace() for char in name) or len(name) > 50:
            flash("Department name can contain only letters and spaces and cannot exceed 50 characters.", "danger")
            return render_template('Admin/admin_dept_edit.html', dept=dept)

        existing_dept = Department.query.filter(Department.name == name, Department.department_id != department_id).first()
        if existing_dept:
            flash("Department name already exists", "danger")
            return render_template('Admin/admin_dept_edit.html', dept=dept)

        dept.name = name
        dept.description = description

        try:
            db.session.commit()
            flash("Department updated successfully!", "success")
        except Exception:
            db.session.rollback()
            flash("An unexpected error occurred while updating the department.", "danger")
        return redirect(url_for('admin.admin_departments'))
        
@admin.route('/delete-department/<int:department_id>')
@login_required            
def admin_delete_department(department_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        dept = Department.query.get(department_id)
        if not dept:
            flash("Department not found!", "danger")
            return redirect(url_for('admin.admin_departments'))

        if len(dept.doctors) > 0:
            flash("Cannot delete department — Doctors are still assigned to it.", "warning")
            return redirect(url_for('admin.admin_departments'))

        try:
            db.session.delete(dept)
            db.session.commit()
            flash("Department deleted successfully!", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while deleting the department.", "danger")
        return redirect(url_for('admin.admin_departments'))

@admin.route('/patients')
@login_required 
def admin_patients():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        search_by = request.args.get('search_by', 'name')  # default = name
        query = request.args.get('query', '').strip()

        patients = Patient.query.join(Patient.user)

        if query:
            if search_by == 'name':
                patients = patients.filter(Patient.name.ilike(f"%{query}%"))
            elif search_by == 'id':
                patients = patients.filter(db.cast(Patient.patient_id, db.String).ilike(f"%{query}%"))
            elif search_by == 'email':
               patients = patients.filter(User.email.ilike(f"%{query}%"))
            elif search_by == 'phone':
                patients = patients.filter(Patient.phone_no.ilike(f"%{query}%"))

        patients = patients.all()

        return render_template('Admin/admin_patients.html',patients=patients,search_by=search_by,query=query)

@admin.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required    
def admin_edit_patient(patient_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    
    patient = Patient.query.get(patient_id)
    if not patient:
        flash("Patient not found!", "danger")

        return redirect(url_for('admin.admin_patients'))
    if request.method == 'GET':
        return render_template('Admin/admin_edit_patient.html', patient=patient)
    elif request.method == 'POST':
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '').strip()
        phone_no = request.form.get('phone_no', '').strip()
        dob_input = request.form.get('dob', '').strip()

        if not all([name, gender, phone_no, dob_input]):
            flash("All required fields must be filled!", "danger")
            return render_template('Admin/admin_edit_patient.html', patient=patient)

        if not all(char.isalpha() or char.isspace() for char in name) or len(name) > 50:
            flash("Name can only contain letters and spaces and must not exceed 50 characters.", "danger")
            return render_template('Admin/admin_edit_patient.html', patient=patient)

        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid gender selected.", "danger")
            return render_template('Admin/admin_edit_patient.html', patient=patient)
  
        try:
            parsed_number = phonenumbers.parse(phone_no, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")
        except Exception:
            flash("Invalid phone number.", "danger")
            return render_template('Admin/admin_edit_patient.html', patient=patient)

        try:
            dob = datetime.strptime(dob_input, "%Y-%m-%d").date()
            if dob > date.today():
                raise ValueError("DOB cannot be in the future")
        except Exception:
            flash("Invalid date of birth.", "danger")
            return render_template('Admin/admin_edit_patient.html', patient=patient)

        patient.name = name
        patient.gender = gender
        patient.phone_no = phone_no
        patient.dob = dob

        try:
            db.session.commit()
            flash("Patient updated successfully!", "success")
        except Exception:
            db.session.rollback()
            flash("Error updating patient.", "danger")

        return redirect(url_for('admin.admin_patients'))
    
@admin.route('/blacklist_patient/<int:patient_id>')
@login_required
def admin_patient_blacklist(patient_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        patient=Patient.query.get(patient_id)
        if not patient:
            flash("Patient not found!", "danger")
            return redirect(url_for('admin.admin_patients'))
        user=User.query.filter_by(user_id=patient.user_id).first()
        
        user.blacklisted=not user.blacklisted 
        if user.blacklisted:
            blacklisted_appts = (
            Appointment.query.filter(Appointment.patient_id == patient.patient_id,  Appointment.status != "cancelled")).all()
        
            for appt in blacklisted_appts:
                appt.status = "cancelled"

        try:
            db.session.commit()
            status = "blacklisted" if user.blacklisted else "removed from blacklist"
            flash(f"Patient has been successfully {status}.", "success")
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the blacklist status.", "danger")

        return redirect(url_for('admin.admin_patients'))
    
@admin.route('/appointments')
@login_required    
def admin_appointments():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        department_id = request.args.get('department_id', '')
        patient_id = request.args.get('patient_id', '')
        doctor_id = request.args.get('doctor_id', '')
        status = request.args.get('status', '')
        query = request.args.get('query', '').strip()

        appointments = (Appointment.query.join(Appointment.doctor).join(Doctor.department).join(Appointment.patient))

        if department_id:
            appointments = appointments.filter(Doctor.department_id == department_id)
        if patient_id:
            appointments = appointments.filter(Appointment.patient_id == patient_id)
        if doctor_id:
            appointments = appointments.filter(Appointment.doctor_id == doctor_id)
        if status:
            appointments = appointments.filter(Appointment.status == status)
        if query:
            appointments = appointments.filter(
            (Doctor.name.ilike(f"%{query}%")) |
            (Patient.name.ilike(f"%{query}%")) |
            (Department.name.ilike(f"%{query}%")))
        
        appointments = appointments.order_by(Appointment.datetime.asc()).all()

        departments = Department.query.all()
        doctors = Doctor.query.all()
        patients = Patient.query.all()

        return render_template(
            'Admin/admin_appointments.html',
            appointments=appointments,
            departments=departments,
            doctors=doctors,
            patients=patients,
            selected_department=department_id,
            selected_doctor=doctor_id,
            selected_patient=patient_id,
            selected_status=status,
            query=query
        )

@admin.route('/appointments_details/<int:appointment_id>')
@login_required    
def admin_appointment_details(appointment_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()

        if not treatment:
            flash("No treatment details found for this appointment.", "warning")
            return redirect(url_for('admin.admin_appointments'))

        return render_template('Admin/admin_appt_view.html',treatment=treatment)