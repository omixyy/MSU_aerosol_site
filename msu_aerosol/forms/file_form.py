from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, SubmitField

from msu_aerosol.config import allowed_extensions

__all__ = []


class FileForm(FlaskForm):
    file = FileField(
        'Файл с данными',
        validators=[
            FileAllowed(
                allowed_extensions,
                'Только csv или xlsx!',
            ),
        ],
    )
    submit = SubmitField('Отправить')
