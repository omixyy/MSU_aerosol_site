from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
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
    name = StringField(
        "Имя пользователя",
        validators=[DataRequired()],
    )
    submit = SubmitField("Отправить")
