import json
import os
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import plotly.offline as offline

__all__ = [
    "load_json",
    "load_graph",
    "preprocessing_one_file",
    "preprocessing_all_files",
    "make_graph",
]


def load_json(path):
    return json.load(open(path, "r"))


def load_graph() -> None:
    data = pd.read_excel(
        "data/AE33-S09-01249/2023_07_AE33-S09-01249.xlsx",
    )
    data["day"] = data["Datetime"].apply(
        lambda x: "-".join(x.split()[0].split(".")[::-1]) + " " + x.split()[1],
    )
    data["day"] = pd.to_datetime(
        data["day"],
        format="%Y-%m-%d %H:%M",
    )
    m = max(data["day"])
    cols = list(set(data.columns.to_list()) - set("Datetime", "date"))
    last_48_hours = [m.replace(day=(m.day - 2)), max(data["day"])]
    fig = px.line(data, x="day", y=cols, range_x=last_48_hours)
    fig.update_layout(legend_itemclick="toggle")
    offline.plot(
        fig,
        filename="templates/graph.html",
        auto_open=False,
    )


def preprocessing_one_file(path):
    _, device, file_name = path.split("/")
    df = pd.read_csv(path, sep=None, engine="python")

    time_col = load_json("config_devices.json")[device]["time_cols"]
    if device == "AE33-S09-01249":
        df[time_col] = pd.to_datetime(df[time_col], format="%d.%m.%Y %H:%M")
    if device == "LVS" or device == "PNS":
        col = list(df.columns)
        df = df.drop("Error", axis=1)
        col.remove("Time")
        df.columns = col
        df[time_col] = pd.to_datetime(df[time_col], format="%d.%m.%Y %H:%M:%S")
    if device == "TCA08":
        df[time_col] = pd.to_datetime(df[time_col], format="%Y-%m-%d %H:%M:%S")
    if device == "Web_MEM":
        df[time_col] = pd.to_datetime(df[time_col], format="%d.%m.%Y %H:%M")
    cols_to_draw = load_json("config_devices.json")[device]["cols"]
    time_col = load_json("config_devices.json")[device]["time_cols"]
    df = df[cols_to_draw + [time_col]]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    """df.set_index(time_col, inplace=True)
    df = df.replace(',', '.', regex=True).astype(float)
    df.reset_index(inplace=True)"""
    name = re.split("[-_]", file_name)
    if not Path(f"proc_data/{device}").exists():
        Path(f"proc_data/{device}").mkdir(parents=True)
    df.to_csv(f"proc_data/{device}/{name[0]}_{name[1]}.csv", index=False)
    return f"proc_data/{device}/{name[0]}_{name[1]}.csv"


def preprocessing_all_files():
    for path in os.listdir("data"):
        for file in os.listdir(f"data/{path}"):
            if file.endswith(".csv"):
                preprocessing_one_file(f"data/{path}/{file}")


def make_graph(device):
    combined_data = pd.DataFrame()
    for i in os.listdir(f"proc_data/{device}"):
        data = pd.read_csv(f"proc_data/{device}/{i}")
        combined_data = pd.concat(
            [combined_data, data],
            ignore_index=True,
        )
        break
    time_col = json.load(open("config_devices.json", "r"))[device]["time_cols"]
    combined_data.set_index(time_col, inplace=True)
    combined_data = combined_data.replace(",", ".", regex=True).astype(float)
    combined_data.reset_index(inplace=True)
    m = pd.to_datetime(max(combined_data[time_col]))
    last_48_hours = [m.replace(day=(m.day - 2)), m]
    cols_to_draw = json.load(open("config_devices.json", "r"))[device]["cols"]
    fig = px.line(
        combined_data,
        x=time_col,
        y=cols_to_draw,
        range_x=last_48_hours,
    )
    fig.update_layout(legend_itemclick="toggle")
    offline.plot(
        fig,
        filename=f"templates/includes/devices/graph_{device}.html",
        auto_open=False,
    )
