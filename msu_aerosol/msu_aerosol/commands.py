import click
from flask import Blueprint
from werkzeug.security import generate_password_hash

from msu_aerosol.models import db, Role, User

__all__ = []

create_superuser: Blueprint = Blueprint("activate", __name__)


@create_superuser.cli.command("createsuperuser")
@click.option("--login", prompt=True)
@click.option("--email", prompt=True)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
def create_superuser(login, email, password):
    admin_role = Role.query.filter_by(name="Admin").first()
    if not admin_role:
        admin_role = Role(
            name="Admin",
            email=email,
            can_access_admin=True,
            can_upload_data=True,
        )
        db.session.add(admin_role)
        db.session.commit()

    user = User(
        login=login,
        password=generate_password_hash(password),
        role_id=admin_role.id,
    )
    db.session.add(user)
    db.session.commit()

    click.echo("Superuser created successfully.")
