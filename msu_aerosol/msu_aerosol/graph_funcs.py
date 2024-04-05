from datetime import timedelta
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from zipfile import ZipFile
import typing as t

import pandas as pd
import plotly.express as px
import plotly.offline as offline
import requests
from yadisk import YaDisk

from msu_aerosol.config import yadisk_token

__all__ = []


def load_json(path: str) -> dict[str, dict[str, t.Any]]:
    return json.load(open(path, "r"))


disk_path = "external_data"
main_path = "data"
disk = YaDisk(token=yadisk_token)
last_modified_file = {}
base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"


def make_format_date(date: str) -> str:
    return "".join(["%" + i if i.isalpha() else i for i in list(date)])


def download_last_modified_file() -> None:
    folder_path = "/external_data"

    for i in disk.listdir(folder_path):
        if i["name"] in load_json("msu_aerosol/config_devices.json").keys():
            last_modified_file = max(
                [
                    file
                    for file in i.listdir()
                    if file["name"].endswith(".csv")
                ],
                key=lambda x: x["modified"],
            )
            download_response = requests.get(last_modified_file["file"])
            Path(f"data/{i['name']}", exist_ok=True).mkdir(parents=True)
            with Path(
                f"data/{i['name']}/{last_modified_file['name']}",
            ).open("wb") as f:
                f.write(download_response.content)


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
    time_col = config_device_open["time_cols"]
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
    ]["time_cols"]
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


def make_graph(
        device: str,
        spec_act,
        begin_record_date=None,
        end_record_date=None,
) -> None:
    resample = "60 min"
    if spec_act == "manual":
        begin_record_date = pd.to_datetime(
            begin_record_date,
            format="%Y-%m-%dT%H:%M:%S",
        )
        end_record_date = pd.to_datetime(
            end_record_date,
            format="%Y-%m-%dT%H:%M:%S",
        )
    device_dict = load_json("msu_aerosol/config_devices.json")[device]
    time_col = device_dict["time_cols"]
    if not begin_record_date or not end_record_date:
        begin_record_date, end_record_date = choose_range(device)
    if spec_act == "recent":
        begin_record_date = end_record_date - timedelta(days=3)
    current_date, combined_data = begin_record_date, pd.DataFrame()
    while current_date <= end_record_date + timedelta(days=100):
        try:
            data = pd.read_csv(
                f"proc_data/{device}/{current_date.strftime('%Y_%m')}.csv",
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
        last_48_hours = None
    combined_data.set_index(time_col, inplace=True)
    combined_data = combined_data.replace(
        ",",
        ".",
        regex=True,
    ).astype(float)
    combined_data = combined_data.resample(resample).mean()
    combined_data.reset_index(inplace=True)
    fig = px.line(
        combined_data,
        x=time_col,
        y=device_dict["cols"],
        range_x=last_48_hours,
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
