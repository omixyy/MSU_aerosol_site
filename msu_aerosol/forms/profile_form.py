from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired

__all__: list = []


class ProfileForm(FlaskForm):
    login = StringField(
        'Логин',
        validators=[DataRequired()],
    )
    name = StringField('Имя')
    surname = StringField('Фамилия')
    email = StringField(
        'Почта',
        validators=[DataRequired()],
    )
    role = StringField(
        'Роль',
        render_kw={
            'readonly': True,
            'disabled': True,
        },
    )
    submit = SubmitField('Сохранить')
