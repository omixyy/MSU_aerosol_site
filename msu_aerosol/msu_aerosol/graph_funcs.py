import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from zipfile import ZipFile

from config import yadisk_token
import pandas as pd
import plotly.express as px
import plotly.offline as offline
import requests
from yadisk import YaDisk

__all__ = []


def load_json(path: str):
    return json.load(open(path, "r"))


config_devices_open = load_json("config_devices.json")
list_devices = list(config_devices_open.keys())
disk_path = "external_data"
main_path = "data"
disk = YaDisk(token=yadisk_token)
last_modified_file = {}
base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"


def download_last_modified_file(device: str) -> None:
    folder_path = "/external_data"
    for i in disk.listdir(folder_path):
        last_modified_file[i["name"]] = max(
            [file for file in i.listdir() if file["name"].endswith(".csv")],
            key=lambda x: x["modified"],
        )
    public_key = last_modified_file[device]["public_url"]
    final_url = base_url + urlencode({"public_key": public_key})
    response = requests.get(final_url)
    download_url = response.json()["href"]

    download_response = requests.get(download_url)
    with Path(f"data/{device}.csv").open("wb") as f:
        f.write(download_response.content)


def download_device_data(url: str) -> str:
    final_url = base_url + urlencode({"public_key": url})
    response = requests.get(final_url)
    download_url = response.json()["href"]
    download_response = requests.get(download_url)
    with Path("yandex_disk_folder.zip").open("wb") as file:
        file.write(download_response.content)
    print("Папка успешно скачана в виде zip архива.")
    with ZipFile("yandex_disk_folder.zip", "r") as zf:
        zf.extractall(f"{main_path}")
        return zf.namelist()[-1][0:-1:]


def pre_proc_device_from_data_to_proc_data(name_folder):
    for name_file in os.listdir(f"{main_path}/{name_folder}"):
        if not name_file.endswith(".csv"):
            Path(f"{main_path}/{name_folder}/{name_file}").unlink()
    for name_file in os.listdir(f"{main_path}/{name_folder}"):
        preprocessing_one_file(f"{main_path}/{name_folder}/{name_file}")


def preprocessing_one_file(path):
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
    return f"proc_data/{device}/{name[0]}_{name[1]}.csv"


def make_graph(device):
    combined_data = pd.DataFrame()
    for i in os.listdir(f"proc_data/{device}"):
        data = pd.read_csv(f"proc_data/{device}/{i}")
        combined_data = pd.concat([combined_data, data], ignore_index=True)
    device_dict = load_json("msu_aerosol/config_devices.json")[device]
    time_col = device_dict["time_cols"]
    m = pd.to_datetime(max(combined_data[time_col]))
    last_48_hours = [m.replace(day=(m.day - 2)), m]
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
        filename=f"templates/includes/devices/full/graph_{device}.html",
        auto_open=False,
    )

    combined_data_48 = combined_data.loc[
        (last_48_hours[0] <= pd.to_datetime(combined_data[time_col]))
        & (pd.to_datetime(combined_data[time_col]) <= last_48_hours[1])
    ]
    fig = px.line(
        combined_data_48,
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
        filename=f"templates/includes/devices/recent/graph_{device}.html",
        auto_open=False,
    )
