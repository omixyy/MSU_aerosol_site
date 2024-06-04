from flask_wtf import FlaskForm
from wtforms import (
    EmailField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired

__all__: list = []


class RegisterForm(FlaskForm):
    """
    Форма регистрации
    """

    login = StringField('Логин', validators=[DataRequired()])
    email = EmailField(
        'Почта',
        validators=[DataRequired()],
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired()],
    )
    password_again = PasswordField(
        'Повторите пароль',
        validators=[DataRequired()],
    )
    submit = SubmitField('Отправить')


class LoginForm(FlaskForm):
    """
    Форма входа в аккаунт
    """

    login = StringField(
        'Логин',
        validators=[DataRequired()],
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired()],
    )
    submit = SubmitField('Войти')
