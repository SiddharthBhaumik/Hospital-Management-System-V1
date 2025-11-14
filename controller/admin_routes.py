from flask import Blueprint,render_template,request,flash,url_for,redirect
from werkzeug.security import generate_password_hash
from controller.models import *
from flask_login import current_user,login_required,logout_user

admin =Blueprint('admin',__name__ )
  
@admin.route('/doctors')
@login_required
def admin_doctors():
    if current_user.role.role != 'Admin':
        return redirect(url_for('main.dashboard'))
    else:
        query = request.args.get('query', '')
        doctors = Doctor.query.join(Department).filter((Doctor.name.ilike(f'%{query}%')) |(Department.name.ilike(f'%{query}%'))).all()
        return render_template('Admin/admin_doctors.html',doctors=doctors)
    
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
                return redirect(url_for('admin.admin_doctors'))
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

@admin.route('/departments/')
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
                return redirect(url_for('admin.admin_department'))
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
            return render_template('Admin/admin_dept_create.html',dept=dept)
        elif request.method=='POST':
            name = request.form.get('name')
            existing_dept=Department.query.filter_by(name=name).first()

            if existing_dept:
                flash("Department name already exists", "danger")
                return render_template('Admin/admin_dept_create.html',dept=dept)
            
            dept.name = name
            dept.desciption = request.form.get('description')

            try:
                db.session.commit()  # save changes to the database
                flash("Department updated successfully!", "success")
                return redirect(url_for('admin.admin_doctors'))
            except Exception as e:
                db.session.rollback()  # rollback in case of error
                flash(f"Error updating department: {e}", "danger")
                return redirect(url_for('admin.admin_departments'))






        






    
        



