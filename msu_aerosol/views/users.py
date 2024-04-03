from datetime import datetime

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug import Response
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from msu_aerosol.admin import get_complexes_dict, login_manager
from forms.auth_forms import LoginForm, RegisterForm
from forms.profile_form import ProfileForm
from msu_aerosol.models import db, User

__all__: list = []


register_bp: Blueprint = Blueprint("register", __name__, url_prefix="/")
login_bp: Blueprint = Blueprint("login", __name__, url_prefix="/")
profile_bp: Blueprint = Blueprint("profile", __name__, url_prefix="/")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def user_profile() -> str:
    complex_to_device = get_complexes_dict()
    form = ProfileForm(obj=current_user)
    if request.method == "POST":
        if form.validate_on_submit():
            current_user.login = request.form.get("login")
            current_user.first_name = request.form.get("first_name")
            current_user.last_name = request.form.get("last_name")
            current_user.email = request.form.get("email")
            db.session.commit()

        return render_template(
            "users/profile.html",
            now=datetime.now(),
            complex_to_device=complex_to_device,
            view_name="profile",
            user=current_user,
            form=form,
            message_success="Данные успешно сохранены",
        )

    return render_template(
        "users/profile.html",
        now=datetime.now(),
        complex_to_device=complex_to_device,
        view_name="profile",
        user=current_user,
        form=form,
    )


@login_bp.route("/login", methods=["GET", "POST"])
def login() -> Response | str:
    complex_to_device = get_complexes_dict()
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(login=form.login.data).first()
            if user:
                if check_password_hash(
                    user.password,
                    form.password.data,
                ):
                    login_user(user)
                    return redirect(url_for("home.index", user=user))

                return render_template(
                    "users/login.html",
                    form=form,
                    message_error="Неверный пароль",
                    complex_to_device=complex_to_device,
                    now=datetime.now(),
                    view_name="login",
                    user=current_user,
                )

            return render_template(
                "users/login.html",
                form=form,
                message_error="Не существует такого пользователя",
                complex_to_device=complex_to_device,
                now=datetime.now(),
                view_name="login",
                user=current_user,
            )

    return render_template(
        "users/login.html",
        form=form,
        complex_to_device=complex_to_device,
        now=datetime.now(),
        view_name="login",
        user=current_user,
    )


@login_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for("home.index"))


@register_bp.route("/register", methods=["GET", "POST"])
def register() -> str | Response:
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

    user_login = request.form.get("login")
    password = request.form.get("password")
    password_again = request.form.get("password_again")
    email = request.form.get("email")
    if password != password_again:
        return render_template(
            "users/register.html",
            form=form,
            message_error="Пароли не совпадают",
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name="registration",
        )

    if User.query.filter_by(login=user_login).first():
        return render_template(
            "users/register.html",
            form=form,
            message_error="Пользователь с таким именем уже существует",
            complex_to_device=complex_to_device,
            now=datetime.now(),
            view_name="registration",
        )

    new_user = User(
        login=user_login,
        password=generate_password_hash(password),
        email=email,
    )

    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return redirect(url_for("home.index"))
