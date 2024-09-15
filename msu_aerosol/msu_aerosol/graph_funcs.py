import asyncio
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.offline as offline
from yadisk import AsyncYaDisk, YaDisk
from yadisk.exceptions import InternalServerError, YaDiskConnectionError

from msu_aerosol.config import yadisk_token
from msu_aerosol.exceptions import ColumnsMatchError, TimeFormatError
from msu_aerosol.models import Device, Graph, TimeColumn, VariableColumn

pd.set_option('future.no_silent_downcasting', True)

__all__ = []

main_path = 'data'
disk_async = AsyncYaDisk(token=yadisk_token)
disk_sync = YaDisk(token=yadisk_token)


def get_device_by_name(name: str, app=None) -> Device | None:
    """
    Функция, которая возвращает объект прибора по его названию
    :param name: имя прибора
    :param app: объект приложения Flask
    """
    if app:
        with app.app_context():
            return Device.query.filter_by(full_name=name).first()

    return Device.query.filter_by(full_name=name).first()


def make_visible_date_format(date: str) -> str:
    """
    Преобразование даты из формата %d.%m.%Y %H:%M:%S в d.m.Y H:M:S
    :param date: дата в формате %d.%m.%Y %H:%M:%S
    :return: дата в формате d.m.Y H:M:S
    """
    return date.replace('%', '')


def make_format_date(date: str) -> str:
    """
    Преобразование даты из формата d.m.Y H:M:S в %d.%m.%Y %H:%M:%S
    :param date: дата в формате d.m.Y H:M:S
    :return: дата в формате %d.%m.%Y %H:%M:%S
    Обратная make_visible_date_format
    """
    return ''.join(['%' + i if i.isalpha() else i for i in list(date)])


def load_colors() -> list:
    """
    Загрузка цветов, использующиеся в окрашивании столбцов, из json файла
    :return: список цветов
    """
    with Path('schema/colors.json').open('r') as colors:
        return json.load(colors)


def no_csv(link: str) -> bool | None:
    """
    Функция, которая определяет, есть ли csv в полученных файлах прибора
    :param link: ссылка, на данные прибора в Я.Диске
    """

    try:
        return all(
            not i['name'].endswith('.csv')
            for i in disk_sync.get_public_meta(link, limit=1000)['embedded'][
                'items'
            ]
        )

    except InternalServerError:
        return None


def download_last_modified_file(name_to_link: dict[str:str], app=None) -> None:
    """
    :param name_to_link: словарь, где ключ - имя прибора,
    значение - ссылка на его данные в Я.Диске
    :param app: объект приложения Flask
    Функция, обновляющая последний измененный файл по каждому прибору
    """
    list_data_path = []
    # Выбор последнего измененного файла по каждому прибору
    for full_name, link in name_to_link.items():
        # Объект последнего измененного файла по прибору
        csv_not_exists = no_csv(link)
        if csv_not_exists is not None:
            last_modified_file = sorted(
                filter(
                    lambda y: y['name'].endswith(
                        '.txt' if csv_not_exists else '.csv',
                    ),
                    disk_sync.get_public_meta(link, limit=1000)['embedded'][
                        'items'
                    ],
                ),
                key=lambda x: x['modified'],
            )[-1]

        else:
            return
        # Путь для сохранения исходного файла.
        file_path = f'{main_path}/{full_name}/{last_modified_file["name"]}'
        try:
            disk_sync.download_by_link(
                last_modified_file['file'],
                file_path,
            )
        except YaDiskConnectionError:
            return
        list_data_path.append([full_name, file_path])
    # Для каждого обновленного файла
    for i in list_data_path:
        dev = get_device_by_name(i[0], app)
        if not dev.archived:  # Если не в архиве
            try:
                if app:
                    with app.app_context():
                        graphs = Graph.query.filter_by(device_id=dev.id)
                else:
                    graphs = Graph.query.filter_by(device_id=dev.id)
                for j in graphs:
                    # Пред обработка обновленного файла
                    preprocessing_one_file(j, i[1], app=app)
                    # Пересоздание полного графика
                    make_graph(j, spec_act='full', app=app)
                    # Пересоздание короткого графика
                    make_graph(j, spec_act='recent', app=app)

            except (KeyError, Exception):
                pass


async def download_file(full_name: str, element: dict) -> None:
    """
    Функция для скачивания файла из Я.Диска
    :param full_name: имя прибора
    :param element: Объект файла, который необходимо скачать
    """
    loop = asyncio.get_event_loop()
    async with disk_async:
        await loop.run_in_executor(
            None,
            disk_sync.download_by_link,
            element['file'],
            f'{main_path}/{full_name}/{element["name"]}',
        )


async def download_device_data(full_name: str, link: str) -> None:
    """
    Функция для загрузки всех данных прибора на сервер с Я.Диска
    :param full_name: имя прибора
    :param link: ссылка на его Я.Диск
    """
    tasks: list = []
    items = disk_sync.get_public_meta(link, limit=1000)
    for i in items['embedded']['items']:
        if not Path(f'{main_path}/{full_name}').exists():
            Path(f'{main_path}/{full_name}').mkdir(parents=True)
        if i['name'].endswith('.csv') or (
            i['name'].endswith('.txt') and no_csv(link)
        ):
            tasks.append(download_file(full_name, i))

    await asyncio.gather(*tasks)


def preprocess_device_data(name_folder: str, graph: Graph, app=None) -> None:
    """
    Функция для пред обработки всех файлов прибора
    :param name_folder: имя папки, где лежат не пред обработанные файлы прибора
    :param graph: объект записи в БД из таблицы graphs
    :param app: объект приложения Flask
    """
    for name_file in os.listdir(f'{main_path}/{name_folder}'):
        preprocessing_one_file(
            graph,
            f'{main_path}/{name_folder}/{name_file}',
            app=app,
        )


def get_time_col(graph: Graph) -> str:
    """
    Функция для определения временного столбца по id графика
    :param graph: объект записи в БД из таблицы graphs
    """
    return (
        TimeColumn.query.filter_by(
            use=True,
            graph_id=graph.id,
        )
        .first()
        .name
    )


def proc_spaces(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    """
    Функция, удаляющая пробелы между большими временными промежутками.
    :param df: Датафрейм, в котором удаляются промежутки
    :param time_col: временной столбец
    """
    df = df.sort_values(by=time_col)
    # diff_mode - временной промежуток между соседними по времени строками,
    # после которого считается, что пробел большой
    diff_mode = df[time_col].diff().mode().values[0] * 1.3
    new_rows = []
    for i in range(len(df) - 1):
        diff = df.loc[i + 1, time_col] - df.loc[i, time_col]
        if diff > diff_mode:
            new_date1 = df.loc[i, time_col] + pd.Timedelta(seconds=1)
            new_date2 = df.loc[i + 1, time_col] - pd.Timedelta(seconds=1)
            new_row1 = {time_col: new_date1}
            new_row2 = {time_col: new_date2}
            new_rows.extend([new_row1, new_row2])
    return pd.concat(
        [df.T.drop_duplicates().T, pd.DataFrame(new_rows)],
        ignore_index=True,
    )


def preprocessing_one_file(
    graph: Graph,
    path: str,
    user_upload=False,
    app=None,
) -> None:
    """
    Функция для пред обработки файла прибора
    :param graph: объект записи в БД из таблицы graphs
    :param path: путь, по которому расположен исходный файл с данными.
    :param user_upload:
    Флаг, отображающий, загружает ли пользователь свои данные
    :param app: Объект приложения Flask
    """
    if app:
        with app.app_context():
            device = Device.query.filter_by(id=graph.device_id).first()
    else:
        device = Device.query.filter_by(id=graph.device_id).first()
    # Считывание датафрейма из файла
    if path.endswith('.csv'):
        df = pd.read_csv(
            path,
            sep=None,
            engine='python',
            decimal=',',
            on_bad_lines='skip',
        )
    else:
        df = pd.read_csv(
            path,
            sep='\t',
            encoding='latin',
            decimal=',',
            on_bad_lines='skip',
        )
    # Если файл пустой, то останавливаем пред обработку
    if df.shape[0] == 0:
        return
    # Получение временного столбца
    if app:
        with app.app_context():
            time_col = get_time_col(graph)
    else:
        time_col = get_time_col(graph)
    # Получение всех столбцов прибора
    columns = [j.name for j in graph.columns if j.use]
    if any(
        (i not in list(df.columns) for i in [time_col] + columns),
    ):
        raise ColumnsMatchError('Проблемы с совпадением столбцов')
    res = [time_col]
    for i in [
        [col.name for col in g.columns if col.use == 1] for g in device.graphs
    ]:
        res += i
    df = df[res]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    if not Path(f'proc_data/{device.name}').exists():
        Path(f'proc_data/{device.name}').mkdir(parents=True)
    # НЕ тривиально: я создаю столбец timestamp,
    # тк дальше это основной временной столбец
    try:
        if time_col == 'timestamp':
            df['timestamp'] = df['timestamp'].apply(
                lambda x: datetime.fromtimestamp(x),
            )
        else:
            df['timestamp'] = pd.to_datetime(
                df[time_col],
                format=make_format_date(graph.time_format),
            )
    except (TypeError, ValueError):
        if not app:
            raise TimeFormatError('Проблемы с форматом времени')
        return
    time_col = 'timestamp'
    # Удаление пробелов
    df = proc_spaces(df, time_col)
    df[time_col] = pd.to_datetime(df[time_col])
    # Перераспределение данных по файлам-месяцам (один файл - один месяц)
    for year in df[time_col].dt.year.unique():
        for month in df[time_col].dt.month.unique():
            df_month = df.loc[
                (
                    (df[time_col].dt.month == month)
                    & (df[time_col].dt.year == year)
                )
            ]
            month = '0' + str(month) if month < 10 else str(month)
            file_path = f'proc_data/{device.name}/{year}_{month}.csv'
            # Если файл уже существовал ранее
            if Path(file_path).exists() or user_upload:
                df_help = pd.read_csv(file_path)
                df_month.loc[:, time_col] = pd.to_datetime(
                    df_month.loc[:, time_col],
                )
                df_help[time_col] = pd.to_datetime(df_help[time_col])
                # Два датафрейма объединяются
                result = pd.merge(df_month, df_help, on=time_col, how='outer')
                for column in df_month.columns:
                    if column in df_help.columns and column != time_col:
                        result[column] = result[column + '_x'].fillna(
                            result[column + '_y'],
                        )
                        result.drop(
                            columns=[column + '_x', column + '_y'],
                            inplace=True,
                        )
                result.drop_duplicates()
                df_month = result
            if len(df_month) == 0:
                continue
            df_month = df_month.sort_values(by=time_col).drop_duplicates(
                subset=[time_col],
            )

            res = [time_col]
            for i in [
                [col.name for col in g.columns if col.use == 1]
                for g in device.graphs
            ]:
                res += i
            # Оставляем только столбцы, которые сейчас используются в приборе
            df_month = df_month[res]
            df_month.to_csv(file_path, index=False)


def choose_range(graph: Graph, app=None) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Функция для вывода границ, которые будут отображаться на графике
    :param graph: объект записи в БД из таблицы graphs
    :param app: объект приложения Flask
    """
    list_files = os.listdir(f'proc_data/{graph.device.name}')
    if app:
        with app.app_context():
            name = Device.query.filter_by(id=graph.device_id).first().name
    else:
        name = Device.query.filter_by(id=graph.device_id).first().name
    proc_data = f'proc_data/{name}/{max(list_files)}'
    max_date = pd.to_datetime(
        pd.read_csv(proc_data)['timestamp'].iloc[-1],
    )
    min_date = max_date - timedelta(days=14)
    return min_date, max_date


def get_spaced_colors(n):
    """
    Функция для возвращения списка различных цветов длиной n
    :param n: длина списка, которой должен быть список
    """
    combined_palette = load_colors()
    return (combined_palette * (n // len(combined_palette) + 1))[:n:]


def make_graph(
    graph: Graph,
    spec_act: str,
    begin_record_date=None,
    end_record_date=None,
    app=None,
) -> None | BytesIO:
    """
    Функция для создания и отрисовки графика
    :param graph: объект записи в БД из таблицы graphs
    :param spec_act: full, recent, download - метка,
    которая отделяет действия только для определенных типов.
    :param begin_record_date: Начальная дата отрисовки графика
    :param end_record_date: конечная дата отрисовки графика
    :param app: объект приложения Flask
    """
    # Если spec_act == 'download', то данные о загрузке поступают с сайта.
    # А begin_record_date и end_record_date из календаря,
    # поэтому необходимо обрабатывать формат времени
    if spec_act == 'download':
        begin_record_date = pd.to_datetime(
            begin_record_date,
            format=(
                '%Y-%m-%dT%H:%M'
                if pd.to_datetime(begin_record_date).second == 0
                else '%Y-%m-%dT%H:%M:%S'
            ),
        )
        end_record_date = pd.to_datetime(
            end_record_date,
            format=(
                '%Y-%m-%dT%H:%M'
                if pd.to_datetime(end_record_date).second == 0
                else '%Y-%m-%dT%H:%M:%S'
            ),
        )
    # Общий временной столбец
    time_col = 'timestamp'
    # Если любая из границ не существует
    if not begin_record_date or not end_record_date:
        begin_record_date, end_record_date = choose_range(graph, app=app)
    # Задаем промежуток прорисовки согласно spec_act
    if spec_act == 'full':
        begin_record_date = end_record_date - timedelta(days=15)
    if spec_act == 'recent':
        begin_record_date = end_record_date - timedelta(days=3)
    current_date, com_data = begin_record_date, pd.DataFrame()
    # Считываем и объединяем файлы,
    # которые могут содержать данные нужные для отрисовки
    while current_date <= end_record_date + timedelta(days=100):
        try:
            data = pd.read_csv(
                f'proc_data/'
                f'{graph.device.name}/'
                f'{current_date.strftime("%Y_%m")}.csv',
            )
            com_data = pd.concat([com_data, data], ignore_index=True)
            current_date += timedelta(days=29)
        except FileNotFoundError:
            current_date += timedelta(days=29)
    com_data[time_col] = pd.to_datetime(com_data[time_col])
    m = max(com_data[time_col])
    last_48_hours = [m - timedelta(days=2), m]
    last_2_weeks = [m - timedelta(days=14), m]
    # Обрезаем com_data согласно временным рамкам в зависимости от spec_act
    if spec_act == 'recent':
        com_data = com_data.loc[
            (last_48_hours[0] <= pd.to_datetime(com_data[time_col]))
            & (pd.to_datetime(com_data[time_col]) <= last_48_hours[1])
        ]
    if spec_act == 'full':
        com_data = com_data.loc[
            (last_2_weeks[0] <= pd.to_datetime(com_data[time_col]))
            & (pd.to_datetime(com_data[time_col]) <= last_2_weeks[1])
        ]
    com_data.set_index(time_col, inplace=True)
    com_data = com_data.replace(
        ',',
        '.',
        regex=True,
    ).astype(float)
    # Доступные столбцы для отрисовки
    cols_to_draw = [i.name for i in graph.columns if i.use]
    # Если spec_act == 'download', то данные сохраняются в формате csv
    if spec_act == 'download':
        buffer = BytesIO()
        com_data.reset_index(inplace=True)
        com_data = com_data.loc[
            (begin_record_date <= pd.to_datetime(com_data[time_col]))
            & (pd.to_datetime(com_data[time_col]) <= end_record_date)
        ]
        com_data.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer

    if spec_act == 'recent' and len(com_data) * len(cols_to_draw) > 500:
        # Для увеличения скорости загрузки и просты интерпретации
        # удаляются выбросы, промежуточные точки и сглаживаются данные
        q1, q3 = com_data.quantile(0.1), com_data.quantile(0.9)
        iqr = com_data.quantile(0.9) - com_data.quantile(0.1)
        lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        filtered_df = com_data[
            ((com_data >= lower_bound) & (com_data <= upper_bound)).all(axis=1)
        ]
        std = filtered_df.std()
        mask = (com_data.diff().abs().div(std) <= 1).all(axis=1)
        consecutive_true = mask & mask.shift(1, fill_value=False)
        mask[(consecutive_true.cumsum() % 2 == 0) & consecutive_true] = False
        com_data.loc[mask, :] = (
            com_data.loc[mask, :].values
            + com_data.loc[mask.shift(-1, fill_value=False), :].values
        ) / 2
        mask_shifted = mask.shift(-1, fill_value=False)
        com_data = com_data[~mask_shifted]
    com_data.reset_index(inplace=True)
    com_data = com_data.drop_duplicates(subset=[time_col])
    com_data = com_data.sort_values(by=time_col)
    # Для упрощения анализа столбцы умножаются на заранее заданные коэффициенты
    if app:
        with app.app_context():
            for i in VariableColumn.query.filter_by(
                graph_id=graph.id,
                use=True,
            ):
                com_data[i.name] = com_data[i.name] * i.coefficient
    else:
        for i in VariableColumn.query.filter_by(graph_id=graph.id, use=True):
            com_data[i.name] = com_data[i.name] * i.coefficient
    # Сортируем столбцы таким образом, чтобы более маленькие рисовались позже
    cols_to_draw = (
        com_data[cols_to_draw]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    index_dict = {value: index for index, value in enumerate(cols_to_draw)}
    # Создание графика столбцов.
    fig = px.line(
        com_data,
        x=time_col,
        y=cols_to_draw,
        color_discrete_sequence=[
            i.color
            for i in sorted(
                [j for j in graph.columns if j.use],
                key=lambda x: index_dict[x.name],
            )
        ],  # цвета столбцов
    )
    cols = graph.columns
    # Если в настройках указано, что столбца изначально не видно, то legendonly
    for trace in fig.data:
        for i in cols:
            if i.name == trace['name']:
                trace.visible = True if i.default else 'legendonly'
                break

    if app:
        with app.app_context():
            full_name = (
                Device.query.filter_by(
                    id=graph.device_id,
                )
                .first()
                .full_name
            )
    else:
        full_name = (
            Device.query.filter_by(
                id=graph.device_id,
            )
            .first()
            .full_name
        )
    # Доступные столбцы для отрисовки
    columns = [i.name for i in graph.columns if i.use]
    # По запросу работодателей мы сделали заливку для BCbb и BCff
    if 'BCbb' in columns or 'BCff' in columns:
        fig.update_traces(fill='tozeroy', line={'width': 2})

    # Настройка макета
    fig.update_layout(
        title=str(full_name),
        xaxis={'title': [i.name for i in graph.time_columns if i.use][0]},
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
    )

    # Настройка осей
    fig.update_xaxes(
        range=[
            datetime.now() - timedelta(2 if spec_act == 'recent' else 14),
            datetime.now(),
        ],
        zerolinecolor='grey',
        zerolinewidth=1,
        gridcolor='grey',
        showline=True,
        linewidth=1,
        linecolor='black',
        mirror=True,
        tickformat='%H:%M\n%d.%m.%Y',
        minor_griddash='dot',
    )
    fig.update_yaxes(
        zerolinecolor='grey',
        zerolinewidth=1,
        gridcolor='grey',
        showline=True,
        linewidth=1,
        linecolor='black',
        mirror=True,
    )

    # Сохранение графика в файл
    offline.plot(
        fig,
        filename=(
            f'templates/'
            f'includes/'
            f'graphs/'
            f'{spec_act}'
            f'/graph_{graph.name}.html'
        ),
        auto_open=False,
        include_plotlyjs=False,
    )

    return None
