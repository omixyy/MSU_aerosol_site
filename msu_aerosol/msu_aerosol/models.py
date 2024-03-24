from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from wtforms.fields import TextAreaField

__all__ = [
    "Complex",
    "Device",
    "db",
]

db: SQLAlchemy = SQLAlchemy()


class Complex(db.Model):
    __tablename__ = "complexes"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    name = db.Column(
        db.String,
    )
    devices = db.relationship(
        "Device",
        backref="Complex",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    name = db.Column(
        db.String,
        nullable=False,
    )
    serial_number = db.Column(
        db.String,
    )
    description = db.Column(
        db.Text,
        nullable=False,
    )
    show = db.Column(
        db.Boolean,
        nullable=False,
    )
    name_on_disk = db.Column(
        db.String,
        nullable=True,
    )
    complex_id = db.Column(
        db.Integer,
        db.ForeignKey("complexes.id"),
        nullable=True,
    )

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name_on_disk


class TextFieldView(ModelView):
    column_list = (
        "id",
        "name",
        "description",
        "serial_number",
    )

    form_overrides = {
        "description": TextAreaField,
    }

    form_widget_args = {
        "description": {
            "rows": 10,
            "style": "width: 500px",
        },
    }

    def description_formatter(self, context, model, name) -> str:
        return (
            model.description[:50] + "..."
            if len(
                model.description,
            )
            > 50
            else model.description
        )

    def on_model_change(self, form, model, is_created) -> None:
        print(type(form), model)
        if is_created:
            ...

    column_formatters = {
        "description": description_formatter,
    }
