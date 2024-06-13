import atexit
import csv
import os
from pathlib import Path
import shutil
from typing import Type

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from flask_admin import Admin
from flask_admin import AdminIndexView, expose
from flask_login import current_user, LoginManager
from sqlalchemy.event import listens_for

from msu_aerosol.exceptions import (
    ColumnsMatchError,
    TimeFormatError,
)
from msu_aerosol.graph_funcs import (
    disk,
    download_device_data,
    download_last_modified_file,
    get_spaced_colors,
    make_graph,
    preprocess_device_data,
)
from msu_aerosol.models import (
    Complex,
    db,
    Device,
    DeviceDataColumn,
    DeviceTimeColumn,
    DeviceView,
    ProtectedView,
    Role,
    User,
    UserFieldView,
)

__all__ = []

application = None


def get_admin_template(
    obj: AdminIndexView,
    error: str | None = None,
    success: str | None = None,
) -> str:
    """
    Функция, возвращающая шаблон домашней страницы админки.

    :param obj: Объект представления админки
    :param error: Сообщение на странице (ошибка)
    :param success: Сообщение на странице (успех)
    :return: Шаблон админки
    """

    return obj.render(
        'admin/admin_home.html',
        name_to_device={
            (
                dev.full_name
                if dev.full_name
                else disk.get_public_meta(dev.link)['name']
            ): dev
            for dev in Device.query.filter_by(archived=False).all()
        },
        message_error=error,
        message_success=success,
    )


class AdminHomeView(AdminIndexView):
    """
    Класс, выступающий в роли представления админки.
    """

    def __init__(self, name=None, url=None) -> None:
        super().__init__(name=name, url=url, template='admin/admin_home.html')

    def is_accessible(self) -> bool:
        return (
            current_user.is_authenticated
            and current_user.role.can_access_admin
        )

    @expose('/', methods=['GET', 'POST'])
    def admin_index(self) -> str:
        """
        Функция, срабатывающая при нажатии на кнопку "подтвердить" в админке.

        :return: Шаблон домашней страницы админки
        """

        downloaded = os.listdir('data')
        downloaded.remove('.gitignore')
        all_devices = Device.query.filter_by(archived=False).all()

        if request.method == 'POST':
            reload = request.form.get('device')
            if reload:
                device_record = Device.query.filter_by(full_name=reload)
                device = device_record.first()
                remove_device_data(reload)

                dev_id = device.id
                name = device.name
                full_name = device.full_name
                link = device.link
                show = device.show
                serial_number = device.serial_number
                archived = device.archived
                complex_id = device.complex_id
                device_record.delete()

                cols = DeviceDataColumn.query.filter_by(device_id=dev_id)
                time_cols = DeviceTimeColumn.query.filter_by(device_id=dev_id)
                cols.delete()
                time_cols.delete()

                new_device = Device(
                    id=dev_id,
                    name=name,
                    full_name=full_name,
                    link=link,
                    show=show,
                    serial_number=serial_number,
                    archived=archived,
                    complex_id=complex_id,
                )
                db.session.add(new_device)
                db.session.commit()
                download_device_data(new_device.link)
                return get_admin_template(
                    self,
                    success='Данные успешно обновлены',
                )

            changed = []
            for dev in all_devices:
                full_name = dev.full_name
                usable_cols = [i.name for i in dev.columns if i.use]
                time_col = [i.name for i in dev.time_columns if i.use]
                default_cols = [
                    i.name
                    for i in DeviceDataColumn.query.filter_by(
                        default=True,
                        device_id=dev.id,
                    ).all()
                ]
                if (
                    request.form.getlist(f'{full_name}_cb') != usable_cols
                    or not usable_cols
                    or not time_col
                    or request.form.get(f'{full_name}_rb') != time_col[0]
                    or request.form.getlist(f'{full_name}_cb_def')
                    != default_cols
                    or request.form.get(f'datetime_format_{full_name}')
                    != dev.time_format
                    or not Path(
                        f'templates/'
                        f'includes/'
                        f'devices/'
                        f'full/'
                        f'graph_{full_name}.html',
                    ).exists()
                ):
                    changed.append(dev)

            for dev in changed:
                full_name = disk.get_public_meta(dev.link)['name']
                checkboxes = request.form.getlist(f'{full_name}_cb')
                radio = request.form.get(f'{full_name}_rb')
                defaults = request.form.getlist(f'{full_name}_cb_def')
                time_format = request.form.get(f'datetime_format_{full_name}')
                if set(defaults).issubset(set(checkboxes)):
                    for col in DeviceDataColumn.query.filter_by(
                        use=True,
                        device_id=dev.id,
                    ):
                        col.use = False
                        col.default = False
                    time_cols = DeviceTimeColumn.query.filter_by(
                        use=True,
                        device_id=dev.id,
                    ).all()
                    for i in time_cols:
                        i.use = False
                    for i in checkboxes:
                        for k in DeviceDataColumn.query.filter_by(
                            name=i,
                            device_id=dev.id,
                        ):
                            k.use = True
                            if i in defaults:
                                k.default = True
                    for j in DeviceTimeColumn.query.filter_by(
                        name=radio,
                        device_id=dev.id,
                    ):
                        j.use = True
                    dev.time_format = time_format
                    dev.full_name = full_name
                    db.session.commit()

                    try:
                        preprocess_device_data(full_name)
                        make_graph(full_name, 'full')
                        make_graph(full_name, 'recent')

                    except TimeFormatError:
                        return get_admin_template(
                            self,
                            error='Формат времени не подходит под столбец',
                        )

                    except ColumnsMatchError:
                        return get_admin_template(
                            self,
                            error='Обнаружено несовпадение столбцов',
                        )

                    except ValueError:
                        return get_admin_template(
                            self,
                            error='Невозможно предобработать данные '
                            'по выбранным столбцам',
                        )

                    except Exception as e:
                        error = e.__class__.__name__
                        return get_admin_template(
                            self,
                            error=f'Непредвиденная ошибка: {error}',
                        )
                else:
                    return get_admin_template(
                        self,
                        error='Не совпадают списки столбцов.',
                    )

            for dev in all_devices:
                dev.show = True
                db.session.commit()

        return get_admin_template(self)


def get_complexes_dict() -> dict[Complex, list[Device]]:
    """
    Функция, возвращающая словарь,
    в котором каждому комплексу сопоставлен список приборов в нём.

    :return: Словарь вида {Комплекс: [*Приборы]}
    """

    return {
        com: Device.query.filter_by(
            complex_id=com.id,
            archived=False,
        ).all()
        for com in Complex.query.all()
    }


def get_dialect(path: str) -> Type[csv.Dialect | csv.Dialect]:
    """
    Функция, возвращающая разделитель в csv файле.

    :param path: Путь к csv файлу
    :return: Разделитель в таблице
    """

    with Path(path).open('r') as f:
        return csv.Sniffer().sniff(f.readline())


@listens_for(Device, 'after_insert')
def after_insert(mapper, connection, target) -> None:
    """
    Функция, срабатывающая после того,
    как в таблицу devices в БД была добавлена запись.

    Определяет полное название прибора через Яндекс диск,
    добавляет столбцам прибора цвета (нужно для Телеграм-бота).

    :param mapper: Необходимый аргумент для декоратора listens_for,
                   не используется в функции
    :param connection: Необходимый аргумент для декоратора listens_for,
                       не используется в функции
    :param target: Необходимый аргумент для декоратора listens_for,
                   представляет собой объект типа Device
    :return: None
    """

    download_device_data(target.link)
    full_name = disk.get_public_meta(target.link)['name']
    file = [
        x
        for x in os.listdir(
            f'data/{full_name}',
        )
        if x.endswith('.csv') or x.endswith('.txt')
    ][0]
    dialect = get_dialect(f'data/{full_name}/{file}')
    with Path(f'data/{full_name}/{file}').open(
        'r',
        encoding='latin' if file.endswith('.txt') else 'utf8',
    ) as csv_file:
        header = list(csv.reader(csv_file, dialect=dialect))[0]
        colors = get_spaced_colors(len(header))

    @listens_for(db.session, 'after_flush', once=True)
    def receive_after_flush(session, context) -> None:
        """
        Вспомогательная функция, присваивает столбцам цвета.

        :param session: Необходимый аргумент для декоратора listens_for,
                        не используется в функции
        :param context: Необходимый аргумент для декоратора listens_for,
                        не используется в функции
        :return: None
        """

        for column, color in zip(header, colors):
            if 'time' in column.lower() or 'date' in column.lower():
                col = DeviceTimeColumn(
                    name=column,
                    device_id=target.id,
                )

                db.session.add(col)

            elif 'time' not in column.lower() or 'date' not in column.lower():
                time_col = DeviceDataColumn(
                    name=column,
                    device_id=target.id,
                    color=color,
                )

                db.session.add(time_col)


def remove_device_data(full_name: str) -> None:
    """
    Удаляет все файлы прибора.

    :param full_name: Полное название прибора
    :return: None
    """

    graph_full = f'templates/includes/devices/full/graph_{full_name}.html'
    graph_rec = f'templates/includes/devices/recent/graph_{full_name}.html'
    proc_data = f'proc_data/{full_name}'
    data = f'data/{full_name}'
    if Path(graph_full).exists():
        Path(graph_full).unlink()

    if Path(graph_rec).exists():
        Path(graph_rec).unlink()

    if Path(proc_data).exists():
        shutil.rmtree(proc_data)

    if Path(data).exists():
        shutil.rmtree(data)


@listens_for(Device, 'after_delete')
def after_delete(mapper, connection, target) -> None:
    """
    Функция, срабатывающая после удаления записи из таблицы devices.
    Удаляет все файлы удаленного прибора.

    :param mapper: Необходимый аргумент для декоратора listens_for,
                   не используется в функции
    :param connection: Необходимый аргумент для декоратора listens_for,
                       не используется в функции
    :param target: Необходимый аргумент для декоратора listens_for,
                   представляет собой объект типа Device
    :return: None
    """

    full_name = disk.get_public_meta(target.link)['name']
    remove_device_data(full_name)


admin: Admin = Admin(
    template_mode='bootstrap4',
    index_view=AdminHomeView(
        name='Home',
        url='/admin',
    ),
)
login_manager: LoginManager = LoginManager()
scheduler: BackgroundScheduler = BackgroundScheduler()
atexit.register(lambda: scheduler.shutdown())


@listens_for(Device, 'after_insert')
@listens_for(Device, 'after_delete')
def init_schedule(mapper, connection, target, app=None) -> None:
    """
    Функция, срабатывающая при удалении или
    добавлении записи в таблицу devices.
    Перезапускает scheduler для избежания ошибок,
    связанных с обновлением несуществующих приборов.

    :param mapper: Необходимый аргумент для декоратора listens_for,
                   не используется в функции
    :param connection: Необходимый аргумент для декоратора listens_for,
                       не используется в функции
    :param target: Необходимый аргумент для декоратора listens_for,
                   представляет собой объект типа Device
    :param app: Объект приложения, нужный для обращения к БД через scheduler
    :return: None
    """

    global scheduler
    global application
    if app:
        application = app
    links: list[str] = [i.link for i in Device.query.all()]
    if scheduler.running or not (mapper and connection and target):
        scheduler.remove_all_jobs()

        scheduler.add_job(
            func=download_last_modified_file,
            trigger='interval',
            seconds=300,
            id='downloader',
            args=[links],
            kwargs={'app': application},
        )

    if not scheduler.running:
        scheduler.start()


def init_admin(app: Flask) -> None:
    """
    Функция инициализации админки.

    :param app: Объект приложения
    :return: None
    """

    login_manager.init_app(app)
    admin.init_app(app)
    admin.add_view(ProtectedView(Complex, db.session))
    admin.add_view(DeviceView(Device, db.session))
    admin.add_view(UserFieldView(User, db.session))
    admin.add_view(ProtectedView(Role, db.session))
