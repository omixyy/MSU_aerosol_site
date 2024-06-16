from datetime import datetime
import re

from flask import (
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from flask.views import MethodView
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
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
    """
    Проверка пароля на безопасность.

    :param password: Сам пароль
    :return: Да/нет
    """

    return not (
        len(password) < 8
        or len(re.findall(r'\d', password)) < 2
        or len(re.findall(r'[a-zA-Z]', password)) < 6
    )


def get_registration_template(error: str | None) -> str:
    """
    Функция, возвращающая шаблон страницы регистрации.

    :param error: Ошибка, если есть. Иначе - None.
    :return: Шаблон страницы регистрации
    """

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
    """
    Функция, возвращающая шаблон страницы профиля.

    :param message: Сообщение об успешном сохранении данных
    :param form: Форма профиля
    :return: Шаблон страницы профиля
    """

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
    """
    Функция, возвращающая шаблон страницы входа.

    :param error: Сообщение об ошибке, если есть. Иначе - None.
    :return: Шаблон страницы входа
    """

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
    """
    Необходимая функция загрузки пользователя.

    :param user_id: Идентификатор пользователя
    :return: Объект пользователя
    """

    return User.query.get(int(user_id))


class Profile(MethodView):
    """
    Представление страницы профиля.
    """

    @login_required
    def get(self) -> str:
        """
        Метод GET для страницы профиля.

        :return: Шаблон страницы профиля с формой
        """
        form = ProfileForm(obj=current_user)
        return get_profile_template(None, form)

    @login_required
    def post(self) -> str:
        """
        Метод POST страницы профиля.
        Сохраняет введённые пользователем данные о себе.

        :return: Шаблон страницы профиля.
        """

        form = ProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.login = request.form.get('login')
            current_user.name = request.form.get('name')
            current_user.surname = request.form.get('surname')
            current_user.email = request.form.get('email')
            db.session.commit()

        return get_profile_template('Данные успешно сохранены', form)


class Login(MethodView):
    """
    Представление страницы входа.
    """

    def get(self) -> str:
        """
        Метод GET для страницы входа.

        :return: Шаблон страницы входа
        """

        return get_login_template(None)

    def post(self) -> str | Response:
        """
        Метод POST для страницы входа.
        Проверяет корректность введённых данных и оформляет вход в систему.

        :return: Редирект на главную, если всё прошло успешно,
                 иначе шаблон страницы входа с ошибкой
        """

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

        return self.get()


class Logout(MethodView):
    """
    Представление выхода из аккаунта.
    """

    @login_required
    def get(self) -> Response:
        """
        Метод GET для выхода из аккаунта, только он доступен.

        :return: Редирект на домашнюю страницу
        """

        logout_user()
        return redirect(url_for('home'))


class Register(MethodView):
    """
    Представление страницы регистрации.
    """

    def get(self) -> str:
        """
        Метод GET для страницы регистрации.

        :return: Шаблон страницы регистрации
        """

        return get_registration_template(None)

    def post(self) -> str | Response:
        """
        Метод POST для страницы регистрации.
        Проверяет корректность всех введённых данных и
        создаёт нового пользователя, если всё хорошо.
        Иначе - сообщение об ошибке.

        :return:
        """

        user_login = request.form.get('login')
        password = request.form.get('password')
        password_again = request.form.get('password_again')
        email = request.form.get('email')
        if password != password_again:
            return get_registration_template('Пароли не совпадают')

        if not is_safe(password):
            return get_registration_template(
                'Пароль должен содержать не менее двух цифр и '
                'не менее шести букв',
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
