from datetime import datetime

from flask import Blueprint, redirect, render_template
from werkzeug.security import check_password_hash, generate_password_hash

from msu_aerosol.admin import get_complexes_dict
from users.forms import RegisterForm

__all__: list = []


def set_password(self, password):
    self.hashed_password = generate_password_hash(password)


def check_password(self, password):
    return check_password_hash(self.hashed_password, password)


register_bp: Blueprint = Blueprint("register", __name__, url_prefix="/")


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    complex_to_device = get_complexes_dict()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template(
                "users/register.html",
                title="Регистрация",
                form=form,
                message="Пароли не совпадают",
                complex_to_device=complex_to_device,
                now=datetime.now(),
                view_name="registration",
            )
        return redirect("/login")

    return render_template(
        "users/register.html",
        title="Регистрация",
        form=form,
        complex_to_device=complex_to_device,
        now=datetime.now(),
        view_name="registration",
    )
