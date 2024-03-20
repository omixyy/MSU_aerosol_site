from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
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
        nullable=True,
    )
    devices = db.relationship(
        "Device",
        backref="Complex",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
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
        nullable=True,
    )
    serial_number = db.Column(
        db.String,
    )
    description = db.Column(
        db.Text,
    )
    complex_id = db.Column(
        db.Integer,
        db.ForeignKey("complexes.id"),
        nullable=True,
    )

    def __repr__(self):
        return self.name


class TextFieldView(ModelView):
    column_list = (
        "id",
        "name",
        "description",
        "serial_number",
    )

    form_overrides = {
        "description": TextAreaField
    }

    form_widget_args = {
        "description": {
            "rows": 10,
            "style": "width: 500px",
        },
    }

    def description_formatter(self, context, model, name):
        return model.description[:50] + '...' if len(
            model.description,
        ) > 50 else model.description
    
    column_formatters = {
        "description": description_formatter,
    }
