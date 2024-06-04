import click
from flask import Blueprint
from werkzeug.security import generate_password_hash

from msu_aerosol.models import db, Role, User

__all__ = []

create_superuser: Blueprint = Blueprint('activate', __name__)


@create_superuser.cli.command('createsuperuser')
@click.option('--login', prompt=True)
@click.option('--email', prompt=True)
@click.option(
    '--password',
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
def create_superuser(login: str, email: str, password: str) -> None:
    """
    Команда создания админа.

    :param login: Логин админа
    :param email: Почта админа
    :param password: Пароль админа
    :return: None
    """

    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        admin_role = Role(
            name='Admin',
            can_access_admin=True,
            can_upload_data=True,
        )
        db.session.add(admin_role)
        db.session.commit()

    user = User(
        login=login,
        email=email,
        password=generate_password_hash(password),
        role_id=admin_role.id,
    )
    db.session.add(user)
    db.session.commit()

    click.echo('Superuser created successfully.')
