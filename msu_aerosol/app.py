import logging

from flask import Flask
from waitress import serve

from msu_aerosol import config
from msu_aerosol.admin import init_admin, init_schedule
from msu_aerosol.commands import create_superuser
from msu_aerosol.models import db
from views.about import About
from views.archive import Archive, DeviceArchive
from views.contacts import ACContacts, DevelopersContacts
from views.graph import GraphDownload, GraphPage
from views.homepage import Home, UpdateIndex
from views.users import Login, Logout, Profile, Register

__all__: list = []


# Важнейшие переменные для управления приложением
app: Flask = config.initialize_flask_app(__name__)

# Настройка приложения
app.cli.add_command(create_superuser)
app.logger.setLevel(logging.INFO)


class NoErrorFilter(logging.Filter):
    """
    Фильтрует ошибки
    """

    def filter(self, record):
        return record.levelno < logging.ERROR


# Отключение логгеров
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).disabled = True

# Настройка логирования
logger = logging.getLogger()  # Получаем корневой логгер
logger.setLevel(logging.DEBUG)

# Удаление всех существующих обработчиков
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Создание нового обработчика для записи логов в файл
file_handler = logging.FileHandler(
    'download_log.log',
    mode='w',
    encoding='utf-8',
)
file_handler.setLevel(logging.INFO)
file_handler.addFilter(NoErrorFilter())
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Связь URL адресов с классами их представления
app.add_url_rule(
    '/',
    view_func=Home.as_view('home'),
)
app.add_url_rule(
    '/about',
    view_func=About.as_view('about'),
)
app.add_url_rule(
    '/archive',
    view_func=Archive.as_view('archive'),
)
app.add_url_rule(
    '/archive/<int:device_id>',
    view_func=DeviceArchive.as_view('device_archive'),
)
app.add_url_rule(
    '/developers_contacts',
    view_func=DevelopersContacts.as_view('developers_contacts'),
)
app.add_url_rule(
    '/contacts',
    view_func=ACContacts.as_view('ac_contacts'),
)
app.add_url_rule(
    '/graphs/<int:graph_id>',
    view_func=GraphPage.as_view('graph'),
)
app.add_url_rule(
    '/graphs/<int:graph_id>/download',
    view_func=GraphDownload.as_view('graph_download'),
)
app.add_url_rule(
    '/profile',
    view_func=Profile.as_view('profile'),
)
app.add_url_rule(
    '/update_index',
    view_func=UpdateIndex.as_view('update_index'),
)
app.add_url_rule(
    '/login',
    view_func=Login.as_view('login'),
)
app.add_url_rule(
    '/logout',
    view_func=Logout.as_view('logout'),
)
app.add_url_rule(
    '/register',
    view_func=Register.as_view('register'),
)

# Создание БД
with app.app_context():
    db.init_app(app)
    db.create_all()
    init_admin(app)
    init_schedule(None, None, None, app=app)


def main() -> None:
    serve(app, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
