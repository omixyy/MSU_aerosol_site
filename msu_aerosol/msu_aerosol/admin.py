import asyncio
import atexit
import csv
import os
from pathlib import Path
import shutil
from typing import Type

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from flask_admin import Admin
from flask_admin import AdminIndexView, BaseView, expose
from flask_login import current_user, LoginManager
from sqlalchemy.event import listens_for

from msu_aerosol.exceptions import (
    ColumnsMatchError,
    TimeFormatError,
)
from msu_aerosol.graph_funcs import (
    download_device_data,
    download_last_modified_file,
    get_spaced_colors,
    make_graph,
    preprocess_device_data,
)
from msu_aerosol.models import (
    Complex,
    ComplexView,
    db,
    Device,
    DeviceView,
    Graph,
    GraphView,
    ProtectedView,
    Role,
    TimeColumn,
    User,
    UserFieldView,
    VariableColumn,
)

__all__ = []

# В эту переменную попадёт объект Flask,
# если будет вызываться функция обновления данных.
# Это необходимо для получения контекста приложения,
# поскольку APScheduler запускает эту функцию в отдельном потоке
application = None


def get_graph_name_to_obj() -> dict:
    return {
        graph.name: graph
        for graph in Graph.query.join(Device)
        .filter(Device.archived == 0)
        .all()
    }


class AdminSettingsView(AdminIndexView):
    """
    Класс, выступающий в роли представления админки.
    """

    def __init__(self, name=None, url=None) -> None:
        super().__init__(
            name=name,
            url=url,
            template='admin/admin_settings.html',
        )

    def get_admin_template(
        self,
        error: str | None = None,
        success: str | None = None,
    ) -> str:
        """
        Функция, возвращающая шаблон домашней страницы админки.

        :param error: Сообщение на странице (ошибка)
        :param success: Сообщение на странице (успех)
        :return: Шаблон админки
        """

        return self.render(
            'admin/admin_settings.html',
            name_to_device=get_graph_name_to_obj(),
            message_error=error,
            message_success=success,
        )

    @classmethod
    def check_if_graph_changed(cls, graph: Graph) -> bool:
        coefficients: list = []
        usable_cols: list = []
        colors: list = []
        for i in graph.columns:
            if i.use:
                colors.append(i)
                coefficients.append(i)
                usable_cols.append(i)

        time_col = TimeColumn.query.filter_by(
            use=True,
            graph_id=graph.id,
        ).first()
        default_cols = [
            i.name
            for i in VariableColumn.query.filter_by(
                default=True,
                graph_id=graph.id,
            )
        ]
        return (
            request.form.getlist(f'{graph.name}_cb') != usable_cols
            or not usable_cols
            or not time_col
            or colors != request.form.getlist(f'color_{graph.name}')
            or request.form.get(f'{graph.name}_rb') != time_col[0]
            or request.form.getlist(f'{graph.name}_cb_def') != default_cols
            or request.form.get(f'datetime_format_{graph.name}')
            != graph.time_format
            or not Path(
                f'templates/'
                f'includes/'
                f'graphs/'
                f'full/'
                f'graph_{graph.name}.html',
            ).exists()
            or not Path(
                f'templates/'
                f'includes/'
                f'graphs/'
                f'recent/'
                f'graph_{graph.name}.html',
            ).exists()
        )

    def recreate_device(self, full_name_reloaded: str) -> str:
        device_record = Device.query.filter_by(
            full_name=full_name_reloaded,
        )
        device = device_record.first()
        remove_device_data(full_name_reloaded)

        dev_id = device.id
        name = device.name
        full_name = device.full_name
        link = device.link
        show = device.show
        serial_number = device.serial_number
        archived = device.archived
        complex_id = device.complex_id
        device_record.delete()

        for graph in Graph.query.filter_by(device_id=dev_id):
            VariableColumn.query.filter_by(graph_id=graph.id).delete()
            TimeColumn.query.filter_by(graph_id=graph.id).delete()

        Graph.query.filter_by(device_id=dev_id).delete()
        new_device: Device = Device(
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
        if os.name == 'nt':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy(),
            )
        asyncio.run(
            download_device_data(
                new_device.full_name,
                new_device.link,
            ),
        )
        init_schedule(None, None, None)
        return self.get_admin_template(
            success='Данные успешно обновлены',
        )

    def is_accessible(self) -> bool:
        return (
            current_user.is_authenticated
            and current_user.role.can_access_admin
        )

    @expose('/', methods=['GET', 'POST'])
    def admin_settings(self) -> str:
        """
        Функция, срабатывающая при нажатии на кнопку "подтвердить"
        в админке или перезагрузке прибора.

        :return: Шаблон домашней страницы админки
        """

        downloaded: list[str] = os.listdir('data')
        all_graphs: list[Device] = Graph.query.all()
        downloaded.remove('.gitignore')

        if request.method == 'POST':
            full_name_reloaded: str = request.form.get('device')
            if full_name_reloaded:
                self.recreate_device(full_name_reloaded)

            changed: list[Device] = []
            for graph in all_graphs:
                if self.check_if_graph_changed(graph):
                    changed.append(graph)

            for graph in changed:
                checkboxes = request.form.getlist(f'{graph.name}_cb')
                radio = request.form.get(f'{graph.name}_rb')
                defaults = request.form.getlist(f'{graph.name}_cb_def')
                time_format = request.form.get(f'datetime_format_{graph.name}')
                colors = request.form.getlist(f'color_{graph.name}')
                coefficients = request.form.getlist(f'coeff_{graph.name}')
                if set(defaults).issubset(set(checkboxes)):
                    for col, color, cf in zip(
                        VariableColumn.query.filter_by(
                            graph_id=graph.id,
                        ),
                        colors,
                        coefficients,
                    ):
                        col.use = col.name in checkboxes
                        col.default = col.name in defaults
                        col.color = color
                        col.coefficient = cf

                    for time_col in TimeColumn.query.filter_by(
                        graph_id=graph.id,
                    ):
                        time_col.use = time_col.name in radio
                    graph.time_format = time_format
                    db.session.commit()
                    try:
                        full_name = (
                            Device.query.filter_by(id=graph.device_id)
                            .first()
                            .full_name
                        )
                        preprocess_device_data(
                            full_name,
                            graph,
                        )
                        make_graph(graph, 'full')
                        make_graph(graph, 'recent')

                    except TimeFormatError:
                        return self.get_admin_template(
                            error='Формат времени не подходит под столбец',
                        )

                    except ColumnsMatchError:
                        return self.get_admin_template(
                            error='Обнаружено несовпадение столбцов',
                        )

                    except ValueError:
                        return self.get_admin_template(
                            error='Невозможно предобработать данные '
                            'по выбранным столбцам',
                        )

                    except Exception as e:
                        error = e.__class__.__name__
                        return self.get_admin_template(
                            error=f'Непредвиденная ошибка: {error}',
                        )
                else:
                    return self.get_admin_template(
                        error='Не совпадают списки столбцов.',
                    )

            for graph in all_graphs:
                graph.device.show = True
                graph.created = True
                db.session.commit()

        return self.get_admin_template()


class AdminLogsView(BaseView):
    def is_accessible(self) -> bool:
        return (
            current_user.is_authenticated
            and current_user.role.can_access_admin
        )

    @expose('/')
    def admin_logs(self):
        with Path('download_log.log').open('r', encoding='utf8') as f:
            file = f.readlines()
        return self.render(
            'admin/admin_logs.html',
            file=file,
            name_to_device=get_graph_name_to_obj(),
        )


def get_complexes_dict() -> dict[Complex, list[Device]]:
    """
    Функция, возвращающая словарь,
    в котором каждому комплексу сопоставлен список приборов в нём.

    :return: Словарь вида {Комплекс: [*Приборы]}
    """

    return {
        com: Graph.query.join(Device)
        .filter(
            Device.complex_id == com.id,
            Device.archived == 0,
        )
        .all()
        for com in Complex.query.all()
    }


def csv_exists(path: str) -> bool:
    return all(i.endswith('.csv') for i in os.listdir(path))


def get_dialect(path: str) -> Type[csv.Dialect | csv.Dialect]:
    """
    Функция, возвращающая разделитель в csv файле.

    :param path: Путь к csv файлу
    :return: Разделитель в таблице
    """

    with Path(path).open(
        'r',
        encoding='utf8' if csv_exists(str(Path(path).parent)) else 'latin',
    ) as f:
        return csv.Sniffer().sniff(f.readline())


def add_columns(graph: Graph, full_name=None) -> None:
    if not full_name:
        full_name = graph.device.full_name
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
        encoding='utf8' if csv_exists(f'data/{full_name}') else 'latin',
    ) as csv_file:
        header = list(csv.reader(csv_file, dialect=dialect))[0]
        colors = get_spaced_colors(len(header))
    for column, color in zip(header, colors):
        if 'time' in column.lower() or 'date' in column.lower():
            time_col = TimeColumn(
                name=column,
                graph_id=graph.id,
            )

            db.session.add(time_col)

        else:
            col = VariableColumn(
                name=column,
                graph_id=graph.id,
                color=(
                    '#ffba42'
                    if column == 'BCbb'
                    else '#3D3C3C' if column == 'BCff' else color
                ),
            )

            db.session.add(col)


@listens_for(Graph, 'after_insert')
def graph_after_insert(mapper, connection, target) -> None:
    @listens_for(db.session, 'after_flush', once=True)
    def receive_after_flush(session, context) -> None:
        add_columns(
            target,
            full_name=Device.query.get(target.device_id).full_name,
        )


@listens_for(Device, 'after_insert')
def device_after_insert(mapper, connection, target) -> None:
    """
    Функция, срабатывающая после того,
    как в таблицу graphs в БД была добавлена запись.

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

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(download_device_data(target.full_name, target.link))

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

        if not target.archived or target.show:
            graph = Graph(
                name=target.full_name,
                device_id=target.id,
            )
            db.session.add(graph)


def remove_device_data(full_name: str) -> None:
    """
    Удаляет все файлы прибора.

    :param full_name: Полное название прибора
    :return: None
    """

    graph_full = f'templates/includes/graphs/full/graph_{full_name}.html'
    graph_rec = f'templates/includes/graphs/recent/graph_{full_name}.html'
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
    Функция, срабатывающая после удаления записи из таблицы graphs.
    Удаляет все файлы удаленного прибора.

    :param mapper: Необходимый аргумент для декоратора listens_for,
                   не используется в функции
    :param connection: Необходимый аргумент для декоратора listens_for,
                       не используется в функции
    :param target: Необходимый аргумент для декоратора listens_for,
                   представляет собой объект типа Device
    :return: None
    """

    full_name = target.full_name
    remove_device_data(full_name)


admin_settings: Admin = Admin(
    template_mode='bootstrap4',
    index_view=AdminSettingsView(
        name='Настройки',
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
    добавлении записи в таблицу graphs.
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
    name_to_link = {
        i.full_name: i.link for i in Device.query.all() if i.show or i.archived
    }
    if scheduler.running or not (mapper and connection and target):
        scheduler.remove_all_jobs()

        scheduler.add_job(
            func=download_last_modified_file,
            trigger='interval',
            seconds=300,
            id='downloader',
            args=[name_to_link],
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
    admin_settings.init_app(app)
    admin_settings.add_view(AdminLogsView(name='Логи', endpoint='/logs'))
    admin_settings.add_view(ComplexView(Complex, db.session, name='Комплексы'))
    admin_settings.add_view(
        DeviceView(
            Device,
            db.session,
            name='Приборы',
            category='Приборы и графики',
        ),
    )
    admin_settings.add_view(
        GraphView(
            Graph,
            db.session,
            name='Графики',
            category='Приборы и графики',
        ),
    )
    admin_settings.add_view(
        UserFieldView(
            User,
            db.session,
            name='Пользователи',
            category='Управление пользователями',
        ),
    )
    admin_settings.add_view(
        ProtectedView(
            Role,
            db.session,
            name='Роли',
            category='Управление пользователями',
        ),
    )
