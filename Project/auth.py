from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, UserLoginLog
from sqlalchemy.sql import func


auth = Blueprint("auth", __name__)



# Login
@auth.route("/login", methods = ['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email = email).first()

        ip_address = request.remote_addr 
        user_agent_str = request.headers.get('User-Agent')




        if user:
            if check_password_hash(user.password, password):
                flash('Login successfull...', category='success')

                session.permanent = True


                login_user(user, remember=True)
                log_status = 'Success'
                user_id_to_log = user.id
                return_redirect = True


                return redirect(url_for('views.admin_panel'))
            
            
            else:
                log_status = 'Failure'
                user_id_to_log = user.id if user else None
                flash('Password is incorrect', category='error') 
                return_redirect = False

            try:
                new_log = UserLoginLog(
                    user_id=user_id_to_log,
                    ip_address=ip_address,
                    user_agent=user_agent_str,
                    status=log_status,
                    
                )
                db.session.add(new_log)
                db.session.commit()
                
            except Exception as e:
                print(f"Failed to log login attempt for email {email}: {e}")
                db.session.rollback()
        
        
        else:
            flash('Email dose not exists', category='error')

    return render_template("login.html", user = current_user)


















# Sign Up
@auth.route("/sign_up", methods = ['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password_again = request.form.get("password-again")

        email_exists = User.query.filter_by(email = email).first()
        name_exsists = User.query.filter_by(username = username).first()

        if email_exists:
            flash('Email is already in use', category='error')
        elif name_exsists:
            flash('Username is already in use', category='error')
        elif password != password_again:
            flash('Password is don\'t match', category='error')
        elif len(username) < 2:
            flash('User name is too short', category='error')
        elif len(password) < 6:
            flash('Password is too short', category='error')
        elif len(email) < 4:
            flash('Email is invalid', category='error')
        else:
            new_user = User(email = email, username = username, password = generate_password_hash(password, method='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('New User account created...')
            return redirect(url_for('auth.login'))


    return render_template("sign.html", user = current_user)


# Logout

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))