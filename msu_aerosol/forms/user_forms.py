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
    login = StringField("Логин", validators=[DataRequired()])
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
    submit = SubmitField("Отправить")


class LoginForm(FlaskForm):
    login = StringField(
        "Логин",
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    submit = SubmitField("Войти")


class ProfileForm(FlaskForm):
    login = StringField(
        "Логин",
        validators=[DataRequired()],
    )
    first_name = StringField("Имя")
    last_name = StringField("Фамилия")
    email = StringField(
        "Почта",
        validators=[DataRequired()],
    )
    admin = StringField(
        "Является ли админом",
        render_kw={
            "readonly": True,
            "disabled": True,
        },
    )
    created_date = StringField(
        "Когда зарегистрирован",
        render_kw={
            "readonly": True,
            "disabled": True,
        },
    )
    can_upload_data = StringField(
        "Может ли загруать данные",
        render_kw={
            "readonly": True,
            "disabled": True,
        },
    )
    submit = SubmitField("Сохранить")
