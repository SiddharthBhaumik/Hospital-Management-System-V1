from flask import Blueprint,render_template,request,flash,url_for,redirect
from controller.models import *
from flask_login import current_user,login_required,logout_user
#from werkzeug.security import generate_password_hash
#from datetime import date

patient =Blueprint('patient',__name__ )