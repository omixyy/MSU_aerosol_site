from datetime import datetime

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import db, User
from users.forms import LoginForm, RegisterForm

__all__: list = []


def set_password(self, password: str) -> None:
    self.hashed_password = generate_password_hash(password)


def check_password(self, password: str) -> bool:
    return check_password_hash(self.hashed_password, password)


register_bp: Blueprint = Blueprint("register", __name__, url_prefix="/")
login_bp: Blueprint = Blueprint("login", __name__, url_prefix="/")


@login_bp.route("/login", methods=["GET", "POST"])
def login() -> str:
    complex_to_device = get_complexes_dict()
    form = LoginForm()
    if request.method == "GET":
        return render_template(
            "users/login.html",
            title="Войти",
            form=form,
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name="login",
            user=current_user,
        )

    return redirect("home.index")


@register_bp.route("/register", methods=["GET", "POST"])
def register() -> str:
    complex_to_device = get_complexes_dict()
    form = RegisterForm()
    if request.method == "GET":
        return render_template(
            "users/register.html",
            title="Регистрация",
            form=form,
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name="registration",
            user=current_user,
        )

    username = request.form.get("username")
    password = request.form.get("password")
    password_again = request.form.get("password_again")
    email = request.form.get("email")
    if password != password_again:
        return render_template(
            "users/register.html",
            form=form,
            error="Пароли не совпадают",
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name="registration",
        )

    if User.query.filter_by(username=username).first():
        return render_template(
            "users/register.html",
            form=form,
            message="Пользователь с таким именем уже существует",
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name="registration",
        )

    new_user = User(
        username=username,
        hashed_password=generate_password_hash(password),
        email=email,
    )

    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for("home.index"))
