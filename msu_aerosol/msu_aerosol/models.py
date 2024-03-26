from datetime import datetime

from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin
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


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    username = db.Column(
        db.String,
        nullable=False,
    )
    email = db.Column(
        db.String,
        index=True,
        unique=True,
        nullable=True,
    )
    hashed_password = db.Column(
        db.String,
        nullable=False,
    )
    created_date = db.Column(
        db.DateTime,
        default=datetime.now(),
    )

    def __repr__(self):
        return f"User ({self.id, self.username})"


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

    column_formatters = {
        "description": description_formatter,
    }
