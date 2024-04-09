from datetime import timedelta
from io import BytesIO
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlencode
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import plotly.offline as offline
import requests
from yadisk import YaDisk

from msu_aerosol.config import yadisk_token

__all__ = []


def load_json(path: str) -> dict[str, dict[str, Any]]:
    return json.load(open(path, "r"))


disk_path = "external_data"
main_path = "data"
disk = YaDisk(token=yadisk_token)
base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"


def make_format_date(date: str) -> str:
    return "".join(["%" + i if i.isalpha() else i for i in list(date)])


def make_visible_date_format(date: str) -> str:
    return date.replace("%", "")


def download_last_modified_file(links: str) -> None:
    list_data_path = []
    for link in links:
        full_name = disk.get_public_meta(link)["name"]
        last_modified_file = sorted(
            disk.get_public_meta(link)["embedded"]["items"],
            key=lambda x: x["modified"],
        )[-1]
        download_response = requests.get(last_modified_file["file"])
        file_path = f'data/{full_name}/{last_modified_file["name"]}'
        list_data_path.append([file_path, full_name])
        with Path(file_path).open("wb") as f:
            f.write(download_response.content)
    for i in list(filter(lambda x: x[0].endswith(".csv"), list_data_path)):
        preprocessing_one_file(i[0])
        make_graph(i[1], spec_act="full")
        make_graph(i[1], spec_act="recent")


def download_device_data(url: str) -> str:
    final_url = base_url + urlencode({"public_key": url})
    response = requests.get(final_url)
    download_url = response.json()["href"]
    download_response = requests.get(download_url)
    with Path("yandex_disk_folder.zip").open("wb") as file:
        file.write(download_response.content)
    with ZipFile("yandex_disk_folder.zip", "r") as zf:
        zf.extractall(f"{main_path}")
        return zf.namelist()[-1][0:-1:]


def preprocess_device_data(name_folder: str) -> None:
    for name_file in os.listdir(f"{main_path}/{name_folder}"):
        if not name_file.endswith(".csv"):
            Path(f"{main_path}/{name_folder}/{name_file}").unlink()
    for name_file in os.listdir(f"{main_path}/{name_folder}"):
        preprocessing_one_file(f"{main_path}/{name_folder}/{name_file}")


def preprocessing_one_file(path: str) -> None:
    config_devices_open = load_json("msu_aerosol/config_devices.json")
    _, device, file_name = path.split("/")
    df = pd.read_csv(path, sep=None, engine="python", decimal=",")
    config_device_open = config_devices_open[device]
    time_col = config_device_open["time_col"]
    df = df[[time_col] + config_device_open["cols"]]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    if not Path(f"proc_data/{device}").exists():
        Path(f"proc_data/{device}").mkdir(parents=True)
    df[time_col] = pd.to_datetime(
        df[time_col],
        format=config_device_open["format"],
    )
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
    df = df.sort_values(by=time_col)
    name = re.split("[-_]", file_name)
    df.to_csv(f"proc_data/{device}/{name[0]}_{name[1]}.csv", index=False)


def choose_range(device: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    time_col = load_json(
        "msu_aerosol/config_devices.json",
    )[
        device
    ]["time_col"]
    list_files = os.listdir(f"proc_data/{device}")
    return (
        pd.to_datetime(
            pd.read_csv(
                f"proc_data/{device}/{min(list_files)}",
            )[
                time_col
            ].iloc[0],
        ),
        pd.to_datetime(
            pd.read_csv(
                f"proc_data/{device}/{max(list_files)}",
            )[
                time_col
            ].iloc[-1],
        ),
    )


def hexx(num: int) -> str:
    return hex(num)[2:].zfill(2)


def get_spaced_colors(n: int) -> list:
    return [
        "#"
        + "".join(
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
) -> None | BytesIO:
    resample = "60 min"
    if spec_act == "download":
        begin_record_date = pd.to_datetime(
            begin_record_date,
            format="%Y-%m-%dT%H:%M"
            if pd.to_datetime(begin_record_date).second == 0
            else "%Y-%m-%dT%H:%M:%S",
        )
        end_record_date = pd.to_datetime(
            end_record_date,
            format="%Y-%m-%dT%H:%M"
            if pd.to_datetime(end_record_date).second == 0
            else "%Y-%m-%dT%H:%M:%S",
        )
    device_dict = load_json("msu_aerosol/config_devices.json")[device]
    time_col = device_dict["time_col"]
    if not begin_record_date or not end_record_date:
        begin_record_date, end_record_date = choose_range(device)
    if spec_act == "recent":
        begin_record_date = end_record_date - timedelta(days=3)
    current_date, combined_data = begin_record_date, pd.DataFrame()
    while current_date <= end_record_date + timedelta(days=100):
        try:
            data = pd.read_csv(
                f'proc_data/{device}/{current_date.strftime("%Y_%m")}.csv',
            )
            combined_data = pd.concat([combined_data, data], ignore_index=True)
            current_date += timedelta(days=29)
        except FileNotFoundError:
            current_date += timedelta(days=29)
    combined_data[time_col] = pd.to_datetime(combined_data[time_col])
    m = max(combined_data[time_col])
    last_48_hours = [m.replace(day=(m.day - 2)), m]
    if spec_act == "recent":
        combined_data = combined_data.loc[
            (last_48_hours[0] <= pd.to_datetime(combined_data[time_col]))
            & (pd.to_datetime(combined_data[time_col]) <= last_48_hours[1])
        ]
    combined_data.set_index(time_col, inplace=True)
    combined_data = combined_data.replace(
        ",",
        ".",
        regex=True,
    ).astype(float)
    if spec_act == "download":
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
        y=device_dict["cols"],
    )
    fig.update_layout(
        title=str(device),
        xaxis={"title": "Time"},
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=True,
    )
    fig.update_traces(line={"width": 2})
    fig.update_xaxes(
        gridcolor="grey",
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
        tickformat="%d.%m.%Y",
    )
    fig.update_yaxes(
        gridcolor="grey",
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
    )
    offline.plot(
        fig,
        filename=(
            f"templates/"
            f"includes/"
            f"devices/"
            f"{spec_act}"
            f"/graph_{device}.html"
        ),
        auto_open=False,
        include_plotlyjs=False,
    )

    return None
