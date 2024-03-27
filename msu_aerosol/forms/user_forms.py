from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired

__all__: list = []


class RegisterForm(FlaskForm):
    email = EmailField(
        "Почта",
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    password_again = PasswordField(
        "Повторите пароль",
        validators=[DataRequired()],
    )
    username = StringField(
        "Имя пользователя",
        validators=[DataRequired()],
    )
    submit = SubmitField("Отправить")


class LoginForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")
