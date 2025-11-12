from flask import Blueprint,render_template,request,redirect, url_for, flash
from flask_login import LoginManager,login_user
from models import User
from werkzeug.security import check_password_hash

auth=Blueprint('auth',__name__)

login_manager=LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/patient_login',methods=['GET','POST'])
def patient_login():
    if request.method=='GET':
        return render_template('patient_login.html')
    if request.method=='POST':
        email= request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter((User.email == email) & (User.username == username)).first()

        if user and check_password_hash(user.password, password) and user.role.role=='Patient':
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('main.dashboard'))  
        else:
            flash("Invalid credentials!", "danger")
            return render_template('patient_login.html')

@auth.route('/staff_login',methods=['GET','POST'])
def staff_login():
    if request.method=='GET':
        return render_template('staff_login.html')
    if request.method=='POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
    
        user = User.query.filter((User.email == email) & (User.username == username)).first()

        if user and check_password_hash(user.password, password) and user.role.role==role:
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('main.dashboard'))  
        else:
            flash("Invalid credentials!", "danger")
            return render_template('staff_login.html')

    


