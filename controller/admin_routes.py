from flask import Blueprint,render_template,request,flash,url_for,redirect
from werkzeug.security import generate_password_hash
from controller.models import *
from flask_login import current_user,login_required

admin =Blueprint('admin',__name__ )
  
@admin.route('/doctors')
@login_required
def admin_doctors():
    if current_user.role.role != 'Admin':
        return redirect(url_for('main.dashboard'))
    else:
        search_by = request.args.get('search_by', 'name')  # default = name
        query = request.args.get('query', '').strip()

        doctors = Doctor.query.join(Doctor.department)

        if query:
            if search_by == 'name':
                doctors = doctors.filter(Doctor.name.ilike(f"%{query}%"))
            elif search_by == 'department':
                doctors = doctors.filter(Department.name.ilike(f"%{query}%"))

        doctors = doctors.all()

        return render_template(
            'Admin/admin_doctors.html',
            doctors=doctors,
            search_by=search_by,
            query=query
        )

    
@admin.route('/add_doctor',methods=['GET','POST'])
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
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            department_id = request.form['department_id']
            experience = request.form['experience']
            about = request.form['about']

            # Check if email already exists
            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash("Email already exists!", "danger")
                return render_template('Admin/admin_doctor_create.html',departments=departments, name=name, experience=experience, about=about, email=email, username=username,department_id=department_id)

# Check if username already exists
            username_exists = User.query.filter_by(username=username).first()
            if username_exists:
                flash("Username already exists!", "danger")
                return render_template('Admin/admin_doctor_create.html', departments=departments,name=name, experience=experience, about=about, email=email, username=username,department_id=department_id)
            
            doctor_role = Roles.query.filter_by(role='Doctor').first()
            doctor_user = User(
                email=email,
                username=username,
                password=generate_password_hash(password),  
                role=doctor_role
            )
            doctor=Doctor(
                name=name, experience=experience, department_id=department_id,about=about,user=doctor_user
            )

            try:
                db.session.add(doctor)
                db.session.commit()
                flash("Doctort added successfully!", "success")
                return redirect(url_for('admin.admin_doctors'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding doctor: {str(e)}", "danger")
                return render_template('Admin/admin_doctor_create.html',departments=departments)
            
@admin.route('/edit_doctor/<int:doctor_id>',methods=['GET','POST'])
@login_required
def admin_doctors_edit(doctor_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        doctor=Doctor.query.get(doctor_id)
        if not doctor:
            flash("Doctor not found!", "danger")
            return redirect(url_for('admin.admin_doctors'))
        
        if request.method=='GET':
            departments=Department.query.all()
            return render_template('Admin/admin_doctor_edit.html',doctor=doctor,departments=departments)
        elif request.method=='POST':
            doctor.name = request.form.get('name')
            doctor.department_id = request.form.get('department_id')  # assuming foreign key
            doctor.experience = request.form.get('experience')
            doctor.about = request.form.get('about')

            try:
                db.session.commit()  # save changes to the database
                flash("Doctor updated successfully!", "success")
            except Exception as e:
                db.session.rollback()  # rollback in case of error
                flash(f"Error updating doctor: {e}", "danger")
            return redirect(url_for('admin.admin_doctors'))

@admin.route('/blacklist_doctor/<int:doctor_id>')
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
        user=User.query.filter_by(user_id=doctor.user_id).first()
        
        user.blacklisted=not user.blacklisted

        try:
            db.session.commit()
            status = "blacklisted" if user.blacklisted else "removed from blacklist"
            flash(f"Doctor has been successfully {status}.", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the blacklist status.", "danger")

        # Redirect back to the doctors list or details page
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

@admin.route('/add_department',methods=['GET','POST'])
@login_required     
def admin_create_department():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        if request.method=='GET':
            return render_template('Admin/admin_dept_create.html')
        elif request.method=='POST':
            name = request.form.get('name')
            description = request.form.get('description')

            existing_dept=Department.query.filter_by(name=name).first()

            if existing_dept:
                flash("Department already exists", "danger")
                return render_template('Admin/admin_dept_create.html',name=name,description=description)
            
            dept=Department(name=name,description=description)
            try:
                db.session.add(dept)
                db.session.commit()
                flash("Department added successfully!", "success")
                return redirect(url_for('admin.admin_departments'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding department: {str(e)}", "danger")
                return render_template('Admin/admin_dept_create.html',name=name,description=description)

@admin.route('/edit_department/<int:department_id>',methods=['GET','POST'])
@login_required            
def admin_edit_department(department_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        dept=Department.query.get(department_id)
        if not dept:
            flash("Department not found!", "danger")
            return redirect(url_for('admin.admin_departments'))
        
        if request.method=='GET':
            return render_template('Admin/admin_dept_edit.html',dept=dept)
        elif request.method=='POST':
            name = request.form.get('name')
            existing_dept=Department.query.filter_by(name=name).first()

            if existing_dept:
                flash("Department name already exists", "danger")
                return render_template('Admin/admin_dept_edit.html',dept=dept)
            
            dept.name = name
            dept.desciption = request.form.get('description')

            try:
                db.session.commit()  # save changes to the database
                flash("Department updated successfully!", "success")
            except Exception as e:
                db.session.rollback()  # rollback in case of error
                flash(f"Error updating department: {e}", "danger")
            return redirect(url_for('admin.admin_departments'))
    
            
@admin.route('/delete_department/<int:department_id>')
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
        except Exception as e:
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

        patients = Patient.query.join(User)

        if query:
            if search_by == 'name':
                patients = patients.filter(Patient.name.ilike(f"%{query}%"))
            elif search_by == 'id':
                patients = patients.filter(Patient.patient_id.ilike(f"%{query}%"))
            elif search_by == 'email':
               patients = patients.filter(User.email.ilike(f"%{query}%"))
            elif search_by == 'phone':
                patients = patients.filter(Patient.phone_no.ilike(f"%{query}%"))

        patients = patients.all()

        return render_template(
            'Admin/admin_patients.html',
            patients=patients,
            search_by=search_by,
            query=query
        )

@admin.route('/edit_patient/<int:patient_id>',methods=['GET','POST'])
@login_required    
def admin_edit_patient(patient_id):
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        patient=Department.query.get(patient_id)
        if not patient:
            flash("Department not found!", "danger")
            return redirect(url_for('admin.admin_departments'))
        
        if request.method=='GET':
            return render_template('Admin/admin_dept_edit.html',patient=patient)
        elif request.method=='POST':
        
            patient.name = request.form.get('name')
            patient.gender = request.form.get('gender')
            patient.phone_no = request.form.get('phone_no')

            try:
                db.session.commit()  # save changes to the database
                flash("Patient updated successfully!", "success")
            except Exception as e:
                db.session.rollback()  # rollback in case of error
                flash(f"Error updating patient: {e}", "danger")
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

        try:
            db.session.commit()
            status = "blacklisted" if user.blacklisted else "removed from blacklist"
            flash(f"Patient has been successfully {status}.", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the blacklist status.", "danger")

        # Redirect back to the doctors list or details page
        return redirect(url_for('admin.admin_patients'))
    
@admin.route('/appointments')
@login_required    
def admin_appointments():
    if current_user.role.role != 'Admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))
    else:
        # ---- GET Filters ----
        department_id = request.args.get('department_id', '')
        patient_id = request.args.get('patient_id', '')
        doctor_id = request.args.get('doctor_id', '')
        status = request.args.get('status', '')
        query = request.args.get('query', '').strip()

        # ---- Base Query (join all needed tables) ----
        appointments = (
            Appointment.query
            .join(Appointment.doctor)     # joins Doctor through relationship
            .join(Doctor.department)      # joins Department through doctor
            .join(Appointment.patient)    # joins Patient
        )

        # ---- Apply filters ----
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