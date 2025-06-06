from flask import render_template, redirect, request, url_for, Blueprint
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from flaskapp import db
from flaskapp import login_manager
from flaskapp.modules.authentication.forms import LoginForm, CreateAccountForm
from flaskapp.modules.authentication.models import Users
from flaskapp.modules.authentication.util import verify_pass

auth_blueprint = Blueprint(
    'authentication_blueprint',
    __name__,
    url_prefix=''
)

@auth_blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('authentication/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('authentication/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('authentication/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('authentication/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        
        # Get a database session
        db.session.add(user)
        db.session.commit()

        return render_template('authentication/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('authentication/register.html', form=create_account_form)


@auth_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@auth_blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@auth_blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@auth_blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
