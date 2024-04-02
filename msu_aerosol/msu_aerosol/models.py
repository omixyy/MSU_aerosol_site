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
        unique=True,
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
        unique=True,
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
    link = db.Column(
        db.String,
        nullable=False,
    )
    complex_id = db.Column(
        db.Integer,
        db.ForeignKey("complexes.id"),
        nullable=True,
    )

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    first_name = db.Column(
        db.String,
        nullable=True,
    )
    last_name = db.Column(
        db.String,
        nullable=True,
    )
    login = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )
    email = db.Column(
        db.String,
        index=True,
        unique=True,
        nullable=True,
    )
    password = db.Column(
        db.String,
        nullable=False,
    )
    created_date = db.Column(
        db.String,
        default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    admin = db.Column(
        db.Boolean,
        default=False,
    )
    can_upload_data = db.Column(
        db.Boolean,
        default=False,
    )

    def __repr__(self):
        return f"User ({self.id, self.login})"


class UserFieldView(ModelView):
    column_list = (
        "id",
        "first_name",
        "last_name",
        "username",
        "email",
        "created_date",
        "admin",
        "can_upload_data",
        "avatar",
    )


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
            "style": "width: 50%",
        },
        "full_name": {
            "readonly": True,
            "disabled": True,
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
