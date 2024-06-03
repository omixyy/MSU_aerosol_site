from datetime import datetime
import re

from flask import (
    make_response,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_restful import Resource
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from forms.auth_forms import LoginForm, RegisterForm
from forms.profile_form import ProfileForm
from msu_aerosol.admin import get_complexes_dict, login_manager
from msu_aerosol.models import db, User

__all__: list = []


def is_safe(password: str) -> bool:
    return not (
        len(password) < 10
        or len(re.findall(r'\d', password)) < 4
        or len(re.findall(r'[a-zA-Z]', password)) < 4
        or len(re.findall(r'[!@#$%^&*()-_+=]', password)) < 2
    )


def get_registration_template(error: str | None) -> Response:
    complex_to_device = get_complexes_dict()
    form = RegisterForm()
    return make_response(
        render_template(
            'users/register.html',
            form=form,
            message_error=error,
            complex_to_device=complex_to_device,
            user=current_user,
            now=datetime.now(),
            view_name='registration',
        ),
        200,
    )


def get_profile_template(message: (str, None), form: ProfileForm) -> Response:
    complex_to_device = get_complexes_dict()
    return make_response(
        render_template(
            'users/profile.html',
            now=datetime.now(),
            complex_to_device=complex_to_device,
            view_name='profile',
            user=current_user,
            form=form,
            message_success=message,
        ),
        200,
    )


def get_login_template(error: (str, None)) -> Response:
    complex_to_device = get_complexes_dict()
    form = LoginForm()
    return make_response(
        render_template(
            'users/login.html',
            form=form,
            message_error=error,
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name='login',
            user=current_user,
        ),
        200,
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Profile(Resource):
    @login_required
    def get(self) -> Response:
        form = ProfileForm(obj=current_user)
        return get_profile_template(None, form)

    @login_required
    def post(self) -> Response:
        form = ProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.login = request.form.get('login')
            current_user.name = request.form.get('name')
            current_user.surname = request.form.get('surname')
            current_user.email = request.form.get('email')
            db.session.commit()

        return get_profile_template('Данные успешно сохранены', form)


class Login(Resource):
    def get(self) -> Response:
        return get_login_template(None)

    def post(self) -> Response:
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(login=form.login.data).first()
            if user:
                if check_password_hash(
                    user.password,
                    form.password.data,
                ):
                    login_user(user)
                    return redirect(url_for('home', user=user))

                return get_login_template('Неверный пароль')

            return get_login_template('Не существует такого пользователя')

        return get_login_template(None)


class Logout(Resource):
    @login_required
    def get(self) -> Response:
        logout_user()
        return redirect(url_for('home'))


class Register(Resource):
    def get(self) -> Response:
        return get_registration_template(None)

    def post(self) -> Response:
        user_login = request.form.get('login')
        password = request.form.get('password')
        password_again = request.form.get('password_again')
        email = request.form.get('email')
        if password != password_again:
            return get_registration_template('Пароли не совпадают')

        if not is_safe(password):
            return get_registration_template(
                'Пароль должен содержать не менее двух цифр и '
                'не менее четырёх букв',
            )

        if User.query.filter_by(login=user_login).first():
            return get_registration_template(
                'Пользователь с таким именем уже существует',
            )

        new_user = User(
            login=user_login,
            password=generate_password_hash(password),
            email=email,
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
