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

from msu_aerosol.config import yadisk_token
from msu_aerosol.exceptions import ColumnsMatchError, TimeFormatError
from msu_aerosol.models import Device, Graph, TimeColumn, VariableColumn

__all__ = []


def get_device_by_name(name: str, app=None) -> Device | None:
    if app:
        with app.app_context():
            return Device.query.filter_by(full_name=name).first()

    return Device.query.filter_by(full_name=name).first()


main_path = 'data'
disk_async = AsyncYaDisk(token=yadisk_token)
disk_sync = YaDisk(token=yadisk_token)


def make_format_date(date: str) -> str:
    return ''.join(['%' + i if i.isalpha() else i for i in list(date)])


def load_colors() -> list:
    with Path('schema/colors.json').open('r') as colors:
        return json.load(colors)


def make_visible_date_format(date: str) -> str:
    return date.replace('%', '')


def no_csv(link: str) -> bool:
    return all(
        not i['name'].endswith('.csv')
        for i in disk_sync.get_public_meta(link, limit=1000)['embedded'][
            'items'
        ]
    )


def download_last_modified_file(name_to_link: dict[str:str], app=None) -> None:
    list_data_path = []
    for full_name, link in name_to_link.items():
        last_modified_file = sorted(
            filter(
                lambda y: y['name'].endswith(
                    '.txt' if no_csv(link) else '.csv',
                ),
                disk_sync.get_public_meta(link, limit=1000)['embedded'][
                    'items'
                ],
            ),
            key=lambda x: x['modified'],
        )[-1]
        file_path = f'data/{full_name}/{last_modified_file["name"]}'
        disk_sync.download_by_link(
            last_modified_file['file'],
            f'{main_path}/{full_name}/{last_modified_file["name"]}',
        )
        list_data_path.append([full_name, file_path])
    for i in list_data_path:
        if app:
            with app.app_context():
                dev = Device.query.filter_by(full_name=i[0]).first()
        else:
            dev = Device.query.filter_by(full_name=i[0]).first()
        if not dev.archived:
            try:
                for j in Graph.query.filter_by(device_id=dev.id).all():
                    preprocessing_one_file(j, i[1], app=app)
                    make_graph(j, spec_act='full', app=app)
                    make_graph(j, spec_act='recent', app=app)

            except (KeyError, Exception):
                pass


async def download_file(full_name: str, element: dict) -> None:
    loop = asyncio.get_event_loop()
    async with disk_async:
        await loop.run_in_executor(
            None,
            disk_sync.download_by_link,
            element['file'],
            f'{main_path}/{full_name}/{element["name"]}',
        )


async def download_device_data(full_name: str, link: str) -> None:
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
    for name_file in os.listdir(f'{main_path}/{name_folder}'):
        preprocessing_one_file(
            graph,
            f'{main_path}/{name_folder}/{name_file}',
            app=app,
        )


def get_time_col(graph_obj):
    return (
        TimeColumn.query.filter_by(
            use=True,
            graph_id=graph_obj.id,
        )
        .first()
        .name
    )


def proc_spaces(df, time_col):
    df = df.sort_values(by=time_col)
    diff_mode = df[time_col].diff().mode().values[0] * 1.1
    new_rows = []
    for i in range(len(df) - 1):
        diff = df.loc[i + 1, time_col] - df.loc[i, time_col]
        if diff > diff_mode:
            new_date1 = df.loc[i, time_col] + pd.Timedelta(seconds=1)
            new_date2 = df.loc[i + 1, time_col] - pd.Timedelta(seconds=1)
            new_row1 = {time_col: new_date1}
            new_row2 = {time_col: new_date2}
            new_rows.extend([new_row1, new_row2])
    return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)


def preprocessing_one_file(
    graph: Graph,
    path: str,
    user_upload=False,
    app=None,
) -> None:
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
    if df.shape[0] == 0:
        return

    if app:
        with app.app_context():
            time_col = get_time_col(graph)
    else:
        time_col = get_time_col(graph)
    columns = [j.name for j in graph.columns if j.use]
    if any(
        (i not in list(df.columns) for i in [time_col] + columns),
    ):
        raise ColumnsMatchError('Проблемы с совпадением столбцов')
    df = df[[time_col] + columns]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    if not Path(f'proc_data/{graph.name}').exists():
        Path(f'proc_data/{graph.name}').mkdir(parents=True)
    try:
        if time_col == 'timestamp':
            df[time_col] = pd.to_datetime(df[time_col], unit='s')
        else:
            df[time_col] = pd.to_datetime(
                df[time_col],
                format=make_format_date(graph.time_format),
            )
    except (TypeError, ValueError):
        if not app:
            raise TimeFormatError('Проблемы с форматом времени')
        return
    df = proc_spaces(df, time_col)
    for year in df[time_col].dt.year.unique():
        for month in df[time_col].dt.month.unique():
            df_month = df.loc[
                (
                    (df[time_col].dt.month == month)
                    & (df[time_col].dt.year == year)
                )
            ]
            month = '0' + str(month) if month < 10 else str(month)
            file_path = f'proc_data/{graph.name}/{year}_{month}.csv'
            if Path(file_path).exists() or user_upload:
                df_help = pd.read_csv(file_path)
                df_help[time_col] = pd.to_datetime(df_help[time_col])
                df_month = pd.concat(
                    [df_help, df_month],
                    ignore_index=True,
                )
                df_month.drop_duplicates()
            if len(df_month) == 0:
                continue
            df_month = df_month.sort_values(by=time_col).drop_duplicates(
                subset=[time_col],
            )
            df_month = df_month[[time_col] + columns]
            df_month.to_csv(file_path, index=False)


def choose_range(graph: Graph) -> tuple[pd.Timestamp, pd.Timestamp]:
    time_col = [i.name for i in graph.time_columns if i.use][0]
    list_files = os.listdir(f'proc_data/{graph.name}')
    proc_data = f'proc_data/{graph.name}/{max(list_files)}'
    max_date = pd.to_datetime(
        pd.read_csv(proc_data)[time_col].iloc[-1],
    )
    min_date = max_date - timedelta(days=14)
    return min_date, max_date


def get_spaced_colors(n):
    combined_palette = load_colors()
    return (combined_palette * (n // len(combined_palette) + 1))[:n:]


def make_graph(
    graph: Graph,
    spec_act: str,
    begin_record_date=None,
    end_record_date=None,
    app=None,
) -> None | BytesIO:
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
    if app:
        with app.app_context():
            time_col = (
                TimeColumn.query.filter_by(
                    graph_id=graph.id,
                    use=True,
                )
                .first()
                .name
            )
    else:
        time_col = (
            TimeColumn.query.filter_by(
                graph_id=graph.id,
                use=True,
            )
            .first()
            .name
        )
    if not begin_record_date or not end_record_date:
        begin_record_date, end_record_date = choose_range(graph)
    if spec_act == 'full':
        begin_record_date = end_record_date - timedelta(days=15)
    if spec_act == 'recent':
        begin_record_date = end_record_date - timedelta(days=3)
    current_date, combined_data = begin_record_date, pd.DataFrame()
    while current_date <= end_record_date + timedelta(days=100):
        try:
            data = pd.read_csv(
                f'proc_data/'
                f'{graph.name}/'
                f'{current_date.strftime("%Y_%m")}.csv',
            )
            combined_data = pd.concat([combined_data, data], ignore_index=True)
            current_date += timedelta(days=29)
        except FileNotFoundError:
            current_date += timedelta(days=29)
    combined_data[time_col] = pd.to_datetime(combined_data[time_col])
    m = max(combined_data[time_col])
    last_48_hours = [m - timedelta(days=2), m]
    last_2_weeks = [m - timedelta(days=14), m]
    if spec_act == 'recent':
        combined_data = combined_data.loc[
            (last_48_hours[0] <= pd.to_datetime(combined_data[time_col]))
            & (pd.to_datetime(combined_data[time_col]) <= last_48_hours[1])
        ]
    if spec_act == 'full':
        combined_data = combined_data.loc[
            (last_2_weeks[0] <= pd.to_datetime(combined_data[time_col]))
            & (pd.to_datetime(combined_data[time_col]) <= last_2_weeks[1])
        ]
    combined_data.set_index(time_col, inplace=True)
    combined_data = combined_data.replace(
        ',',
        '.',
        regex=True,
    ).astype(float)
    if spec_act == 'download':
        buffer = BytesIO()
        combined_data.reset_index(inplace=True)
        combined_data = combined_data.loc[
            (begin_record_date <= pd.to_datetime(combined_data[time_col]))
            & (pd.to_datetime(combined_data[time_col]) <= end_record_date)
        ]
        combined_data.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer

    if spec_act == 'recent':
        q1, q3 = combined_data.quantile(0.1), combined_data.quantile(0.9)
        iqr = combined_data.quantile(0.9) - combined_data.quantile(0.1)
        lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        filtered_df = combined_data[
            (
                (combined_data >= lower_bound) & (combined_data <= upper_bound)
            ).all(axis=1)
        ]
        std = filtered_df.std()
        mask = (combined_data.diff().abs().div(std) <= 1).all(axis=1)
        consecutive_true = mask & mask.shift(1, fill_value=False)
        mask[(consecutive_true.cumsum() % 2 == 0) & consecutive_true] = False
        combined_data.loc[mask, :] = (
            combined_data.loc[mask, :].values
            + combined_data.loc[mask.shift(-1, fill_value=False), :].values
        ) / 2
        mask_shifted = mask.shift(-1, fill_value=False)
        combined_data = combined_data[~mask_shifted]
    combined_data.reset_index(inplace=True)
    combined_data = combined_data.drop_duplicates(subset=[time_col])
    combined_data = combined_data.sort_values(by=time_col)
    for i in VariableColumn.query.filter_by(graph_id=graph.id, use=True):
        combined_data[i.name] = combined_data[i.name] * i.coefficient
    cols_to_draw = [i.name for i in graph.columns if i.use]
    cols_to_draw = (
        combined_data[cols_to_draw]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    index_dict = {value: index for index, value in enumerate(cols_to_draw)}
    fig = px.line(
        combined_data,
        x=time_col,
        y=cols_to_draw,
        color_discrete_sequence=[
            i.color
            for i in sorted(
                [j for j in graph.columns if j.use],
                key=lambda x: index_dict[x.name],
            )
        ],
    )
    cols = graph.columns
    for trace in fig.data:
        for i in cols:
            if i.name == trace['name']:
                trace.visible = True if i.default else 'legendonly'
                break

    fig.update_layout(
        title=str(graph.device.full_name),
        xaxis={'title': [i.name for i in graph.time_columns if i.use][0]},
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
    )
    fig.update_traces(line={'width': 2})
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
