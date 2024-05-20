from datetime import timedelta
from io import BytesIO
import os
from pathlib import Path
from urllib.parse import urlencode
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import plotly.offline as offline
import requests
from yadisk import YaDisk

from msu_aerosol.config import yadisk_token
from msu_aerosol.exceptions import ColumnsMatchError, TimeFormatError
from msu_aerosol.models import Device

__all__ = []


def get_device_by_name(name: str, app=None) -> Device | None:
    if app:
        with app.app_context():
            return Device.query.filter_by(full_name=name).first()

    return Device.query.filter_by(full_name=name).first()


main_path = 'data'
disk = YaDisk(token=yadisk_token)
base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'


def make_format_date(date: str) -> str:
    return ''.join(['%' + i if i.isalpha() else i for i in list(date)])


def make_visible_date_format(date: str) -> str:
    return date.replace('%', '')


def download_last_modified_file(links, app=None) -> None:
    print("DOWNLOADING")
    list_data_path = []
    for link in links:
        full_name = disk.get_public_meta(link)['name']
        last_modified_file = sorted(
            filter(
                lambda y: y['name'].endswith('.csv'),
                disk.get_public_meta(link)['embedded']['items'],
            ),
            key=lambda x: x['modified'],
        )[0]
        download_response = requests.get(last_modified_file['file'])
        file_path = f'data/{full_name}/{last_modified_file["name"]}'
        list_data_path.append([full_name, file_path])
        with Path(file_path).open('wb') as f:
            f.write(download_response.content)
    for i in list_data_path:
        try:
            preprocessing_one_file(i[0], i[1], app=app)
            make_graph(i[0], spec_act='full', app=app)
            make_graph(i[0], spec_act='recent', app=app)

        except (KeyError, Exception):
            pass


def download_device_data(url: str) -> str:
    final_url = base_url + urlencode({'public_key': url})
    response = requests.get(final_url)
    download_url = response.json()['href']
    download_response = requests.get(download_url)
    with Path('yandex_disk_folder.zip').open('wb') as file:
        file.write(download_response.content)
    with ZipFile('yandex_disk_folder.zip', 'r') as zf:
        zf.extractall(f'{main_path}')
        return zf.namelist()[-1][0:-1:]


def preprocess_device_data(name_folder: str) -> None:
    for name_file in os.listdir(f'{main_path}/{name_folder}'):
        if not name_file.endswith('.csv'):
            Path(f'{main_path}/{name_folder}/{name_file}').unlink()
    for name_file in os.listdir(f'{main_path}/{name_folder}'):
        preprocessing_one_file(
            name_folder,
            f'{main_path}/{name_folder}/{name_file}',
        )


def preprocessing_one_file(
    device: str,
    path: str,
    user_upload=False,
    app=None,
) -> None:
    df = pd.read_csv(path, sep=None, engine='python', decimal=',')
    device_obj = get_device_by_name(device, app=app)
    time_col = list(filter(lambda x: x.use, device_obj.time_columns))[0].name
    columns = [j.name for j in device_obj.columns if j.use]
    if any(
        (i not in list(df.columns) for i in [time_col] + columns),
    ):
        raise ColumnsMatchError('Проблемы с совпадением столбцов')
    df = df[[time_col] + columns]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    if not Path(f'proc_data/{device}').exists():
        Path(f'proc_data/{device}').mkdir(parents=True)
    try:
        df[time_col] = pd.to_datetime(
            df[time_col],
            format=make_format_date(device_obj.time_format),
        )
    except (TypeError, ValueError):
        if not app:
            raise TimeFormatError('Проблемы с форматом времени')
        return
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
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    for year in df[time_col].dt.year.unique():
        for month in df[time_col].dt.month.unique():
            df_month = df.loc[
                (
                    (df[time_col].dt.month == month)
                    & (df[time_col].dt.year == year)
                )
            ]
            month = '0' + str(month) if month < 10 else str(month)
            file_path = f'proc_data/{device}/{year}_{month}.csv'
            if Path(file_path).exists() and user_upload:
                df_help = pd.read_csv(file_path)
                df_help[time_col] = pd.to_datetime(df_help[time_col])
                df_month = pd.concat(
                    [df_help, df_month],
                    ignore_index=True,
                )
                df_month.drop_duplicates()
            if len(df_month) == 0:
                continue
            df_month = df_month.sort_values(by=time_col)
            df_month.to_csv(file_path, index=False)


def choose_range(device: str, app=None) -> tuple[pd.Timestamp, pd.Timestamp]:
    time_col = [
        i.name
        for i in get_device_by_name(device, app=app).time_columns
        if i.use
    ][0]
    list_files = os.listdir(f'proc_data/{device}')
    return (
        pd.to_datetime(
            pd.read_csv(
                f'proc_data/{device}/{min(list_files)}',
            )[
                time_col
            ].iloc[0],
        ),
        pd.to_datetime(
            pd.read_csv(
                f'proc_data/{device}/{max(list_files)}',
            )[
                time_col
            ].iloc[-1],
        ),
    )


def hexx(num: int) -> str:
    return hex(num)[2:].zfill(2)


def get_spaced_colors(n: int) -> list:
    return [
        '#'
        + ''.join(
            (
                hexx(int(i[:2], 16)),
                hexx(int(i[2:4], 16)),
                hexx(int(i[4:], 16)),
            ),
        ).upper()
        for i in [
            hex(j)[2:].zfill(6)
            for j in range(
                int(16581375 / n),
                16581375,
                int(16581375 / n),
            )
        ]
    ]


def make_graph(
    device: str,
    spec_act,
    begin_record_date=None,
    end_record_date=None,
    app=None,
) -> None | BytesIO:
    resample = '60 min'
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
    device_obj = get_device_by_name(device, app=app)
    time_col = list(filter(lambda x: x.use, device_obj.time_columns))[0].name
    if not begin_record_date or not end_record_date:
        begin_record_date, end_record_date = choose_range(device, app=app)
    if spec_act == 'recent':
        begin_record_date = end_record_date - timedelta(days=3)
    current_date, combined_data = begin_record_date, pd.DataFrame()
    while current_date <= end_record_date + timedelta(days=100):
        try:
            data = pd.read_csv(
                f'proc_data/'
                f'{device}/'
                f'{current_date.strftime("%Y_%m")}.csv',
            )
            combined_data = pd.concat([combined_data, data], ignore_index=True)
            current_date += timedelta(days=29)
        except FileNotFoundError:
            current_date += timedelta(days=29)
    combined_data[time_col] = pd.to_datetime(combined_data[time_col])
    m = max(combined_data[time_col])
    last_48_hours = [m.replace(day=(m.day - 2)), m]
    if spec_act == 'recent':
        combined_data = combined_data.loc[
            (last_48_hours[0] <= pd.to_datetime(combined_data[time_col]))
            & (pd.to_datetime(combined_data[time_col]) <= last_48_hours[1])
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
    combined_data = combined_data.resample(resample).mean()
    combined_data.reset_index(inplace=True)
    fig = px.line(
        combined_data,
        x=time_col,
        y=[i.name for i in device_obj.columns if i.use],
    )
    fig.update_layout(
        title=str(device),
        xaxis={'title': 'Time'},
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
    )
    fig.update_traces(line={'width': 2})
    fig.update_xaxes(
        gridcolor='grey',
        showline=True,
        linewidth=1,
        linecolor='black',
        mirror=True,
        tickformat='%d.%m.%Y',
    )
    fig.update_yaxes(
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
            f'devices/'
            f'{spec_act}'
            f'/graph_{device}.html'
        ),
        auto_open=False,
        include_plotlyjs=False,
    )

    return None
