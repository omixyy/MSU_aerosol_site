from datetime import datetime
import re

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug import Response
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from forms.auth_forms import LoginForm, RegisterForm
from forms.profile_form import ProfileForm
from msu_aerosol.admin import get_complexes_dict, login_manager
from msu_aerosol.models import db, User

__all__: list = []


register_bp: Blueprint = Blueprint('register', __name__, url_prefix='/')
login_bp: Blueprint = Blueprint('login', __name__, url_prefix='/')
profile_bp: Blueprint = Blueprint('profile', __name__, url_prefix='/')


def is_safe(password: str) -> bool:
    return not (
        len(password) < 10
        or len(re.findall(r'\d', password)) < 4
        or len(re.findall(r'[a-zA-Z]', password)) < 4
        or len(re.findall(r'[!@#$%^&*()-_+=]', password)) < 2
    )


def get_registration_template(error: str | None) -> str:
    complex_to_device = get_complexes_dict()
    form = RegisterForm()
    return render_template(
        'users/register.html',
        form=form,
        message_error=error,
        complex_to_device=complex_to_device,
        user=current_user,
        now=datetime.now(),
        view_name='registration',
    )


def get_profile_template(message: str | None, form: ProfileForm) -> str:
    complex_to_device = get_complexes_dict()
    return render_template(
        'users/profile.html',
        now=datetime.now(),
        complex_to_device=complex_to_device,
        view_name='profile',
        user=current_user,
        form=form,
        message_success=message,
    )


def get_login_template(error: str | None) -> str:
    complex_to_device = get_complexes_dict()
    form = LoginForm()
    return render_template(
        'users/login.html',
        form=form,
        message_error=error,
        complex_to_device=complex_to_device,
        now=datetime.now(),
        view_name='login',
        user=current_user,
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile() -> str:
    form = ProfileForm(obj=current_user)
    if request.method == 'POST':
        if form.validate_on_submit():
            current_user.login = request.form.get('login')
            current_user.name = request.form.get('name')
            current_user.surname = request.form.get('surname')
            current_user.email = request.form.get('email')
            db.session.commit()

        return get_profile_template('Данные успешно сохранены', form)

    return get_profile_template(None, form)


@login_bp.route('/login', methods=['GET', 'POST'])
def login() -> Response | str:
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(login=form.login.data).first()
            if user:
                if check_password_hash(
                    user.password,
                    form.password.data,
                ):
                    login_user(user)
                    return redirect(url_for('home.index', user=user))

                return get_login_template('Неверный пароль')

            return get_login_template('Не существует такого пользователя')

    return get_login_template(None)


@login_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for('home.index'))


@register_bp.route('/register', methods=['GET', 'POST'])
def register() -> str | Response:
    if request.method == 'GET':
        return get_registration_template(None)

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
    return redirect(url_for('home.index'))
