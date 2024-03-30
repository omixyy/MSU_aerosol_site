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
    submit = SubmitField("Войти")


class ProfileForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[DataRequired()],
    )
    first_name = StringField("Имя")
    last_name = StringField("Фамилия")
    email = StringField(
        "Почта",
        validators=[DataRequired()],
    )
    is_admin = StringField(
        "Является ли админом",
        render_kw={"readonly": True},
    )
    created_date = StringField(
        "Когда зарегистрирован",
        render_kw={"readonly": True},
    )
    can_upload_data = StringField(
        "Может ли загруать данные",
        render_kw={"readonly": True},
    )
    submit = SubmitField("Сохранить")
