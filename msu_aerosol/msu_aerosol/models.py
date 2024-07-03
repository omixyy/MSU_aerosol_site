from datetime import datetime

from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.orm import declared_attr

__all__ = []

db: SQLAlchemy = SQLAlchemy()


class BaseModel(db.Model):
    """
    Базовая модель.
    """

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)


class ProtectedView(ModelView):
    def is_accessible(self) -> bool:
        return (
            current_user.is_authenticated
            and current_user.role.can_access_admin
        )


class BaseColumnModel(db.Model):
    """
    Базовая модель для столбца.
    """

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=False)
    use = db.Column(db.Boolean, nullable=False, default=False)

    @declared_attr
    def graph_id(self) -> sqlalchemy.Column:
        """
        Поле, связанное с id прибора.

        :return: Идентификатор прибора
        """

        return db.Column(
            db.Integer,
            db.ForeignKey('graphs.id'),
            nullable=False,
        )


class Complex(BaseModel):
    """
    Таблица комплексов приборов.
    """

    __tablename__ = 'complexes'
    devices = db.relationship(
        'Device',
        backref='complex',
        lazy=True,
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class Device(BaseModel):
    """
    Таблица приборов.
    """

    __tablename__ = 'devices'
    name = db.Column(db.String, unique=True, nullable=False)
    serial_number = db.Column(db.String, default='')
    show = db.Column(db.Boolean, nullable=True, default=False)
    link = db.Column(db.String, nullable=False)
    archived = db.Column(db.Boolean, default=False)
    graphs = db.relationship(
        'Graph',
        backref='device',
        lazy='subquery',
        cascade='all, delete-orphan',
    )
    full_name = db.Column(
        db.String,
        default=lambda context: (
            f'{context.get_current_parameters()["name"]}'
            f' {context.get_current_parameters()["serial_number"]}'
            if context.get_current_parameters()['serial_number']
            else f'{context.get_current_parameters()["name"]}'
        ),
    )
    complex_id = db.Column(
        db.Integer,
        db.ForeignKey('complexes.id'),
        nullable=True,
    )

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class User(BaseModel, UserMixin):
    """
    Таблица пользователей.
    """

    __tablename__ = 'users'
    name = db.Column(db.String, unique=False)
    surname = db.Column(db.String, nullable=True)
    login = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, index=True, unique=True, nullable=True)
    password = db.Column(db.String, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    created_date = db.Column(
        db.String,
        default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )

    def __repr__(self) -> str:
        return self.login


class Role(BaseModel):
    """
    Таблица ролей пользователей.
    """

    __tablename__ = 'roles'
    can_access_admin = db.Column(db.Boolean, default=False)
    can_upload_data = db.Column(db.Boolean, default=False)
    can_download_data = db.Column(db.Boolean, default=False)

    users = db.relationship(
        'User',
        backref='role',
        lazy=True,
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return self.name


class Graph(BaseModel):
    __tablename__ = 'graphs'

    device_id = db.Column(
        db.Integer,
        db.ForeignKey('devices.id'),
        nullable=True,
    )
    time_format = db.Column(db.String, nullable=True)
    created = db.Column(
        db.Boolean,
        default=False,
    )
    columns = db.relationship(
        'VariableColumn',
        backref='graph',
        lazy='subquery',
        cascade='all, delete-orphan',
    )
    time_columns = db.relationship(
        'TimeColumn',
        backref='graph',
        lazy='subquery',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return self.name


class VariableColumn(BaseColumnModel):
    """
    Таблица столбцов.
    """

    __tablename__ = 'columns'
    color = db.Column(db.String)
    default = db.Column(db.Boolean, default=False)
    coefficient = db.Column(db.Integer, default=1)


class TimeColumn(BaseColumnModel):
    """
    Таблица столбцов времени.
    """

    __tablename__ = 'time_columns'


class UserFieldView(ProtectedView):
    """
    Эти поля бут отображаться в админке в таблице пользователей.
    """

    column_list = [
        'id',
        'login',
        'name',
        'surname',
        'email',
        'created_date',
    ]

    form_excluded_columns = ('password',)


class DeviceView(ProtectedView):
    """
    Эти поля бут отображаться в админке в таблице приборов.
    """

    column_list = [
        'id',
        'name',
        'full_name',
        'serial_number',
        'complex_id',
        'graphs',
    ]
    form_excluded_columns = (
        'show',
        'columns',
        'time_format',
        'time_columns',
        'full_name',
    )


class ComplexView(ProtectedView):
    column_list = [
        'id',
        'name',
        'devices',
    ]


class GraphView(ProtectedView):
    form_excluded_columns = (
        'created',
        'time_columns',
        'columns',
        'time_format',
    )
