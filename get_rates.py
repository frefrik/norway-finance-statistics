import json
from datetime import date, datetime, timedelta
from io import StringIO
from os import path

import pandas as pd
import requests

from src.finansportalen import Mortgage


def write_df(dataset, df):
    try:
        df.to_csv("./data/" + dataset + ".csv", encoding="utf-8", index=False)
        print("DataFrame updated: {}".format(dataset))
    except Exception:
        print("write_df: Error")


def get_dates(lastdate):
    date_today = date.today()
    delta_date = date_today - timedelta(days=(date_today - lastdate).days)
    delta_days = (date_today - lastdate).days

    return date_today, delta_date, delta_days


def write_last_updated(dataset):
    with open("datasets.json", "r") as read_file:
        datasets = json.load(read_file)

    array = list(filter(lambda x: x["dataset"] == dataset, datasets))
    array[0]["last_updated"] = str(date.today())

    with open("datasets.json", "w") as f:
        json.dump(datasets, f, indent=2)


def mortgage():
    dataset = "no_mortgage"
    params = {
        "lanebelop": 5000000,
        "boligverdi": 7200000,
        "nedbetalingstid": 20,
        "alder": 36,
        "rentetype": "flytende_rente",
        "markedsomrade": "nasjonalt",
        "medlemskap": "nei",
        "n": 10,
    }

    if path.exists(f"./data/{dataset}.csv"):
        df = pd.read_csv(f"./data/{dataset}.csv", parse_dates=["date"])
        date_last = max(df["date"]).date()
    else:
        df = pd.DataFrame()
        date_last = date.today() - timedelta(days=1)

    delta = get_dates(date_last)

    if delta[2] > 0:
        df_new = Mortgage(params).get_dataframe()
        df = pd.concat([df, df_new], ignore_index=True)

        write_df(dataset, df)
        write_last_updated(dataset)
    else:
        print("Data already up to date:", dataset)


def nibor():
    dataset_n = "no_nibor"
    dataset_np = "no_nibor_panel"

    if path.exists("./data/" + dataset_np + ".csv"):
        df_panel = pd.read_csv(
            "./data/" + dataset_np + ".csv", parse_dates=["Date", "Calculation Date"]
        )
        date_last = max(df_panel["Date"]).date() + timedelta(days=1)
    else:
        df_panel = pd.DataFrame()
        date_last = datetime(2020, 1, 1).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        for i in range(delta[2]):
            day = date_last + timedelta(days=i)
            res = requests.post(
                "https://nibor.globalrateset.com/submit.php",
                data={"market": "NIBOR", "date": day},
            )
            load = json.loads(res.content)

            if load["status"] == "ok":
                print(day, "Fetching new data")
                array = load["results"]
                df_panel_new = pd.DataFrame(array)
                df_panel_new.insert(0, "Date", day)
                df_panel = df_panel.append(df_panel_new)
            elif load["message"] == "Invalid request date":
                print(day, "No rates published on this date")

                df_panel_new = pd.DataFrame(
                    {
                        "Date": [day] * 5,
                        "Calculation Date": [day] * 5,
                        "Tenor": [
                            "1 Week",
                            "1 Month",
                            "2 Months",
                            "3 Months",
                            "6 Months",
                        ],
                    }
                )
                df_panel = df_panel.append(df_panel_new)
            else:
                print(day, "Unknown error, skipping")
                pass

        df_panel["Date"] = pd.to_datetime(df_panel["Date"])
        df_panel["Calculation Date"] = pd.to_datetime(df_panel["Calculation Date"])

        df_fixed = df_panel.pivot(
            index="Date", columns="Tenor", values="Fixing Rate"
        ).reset_index()
        df_fixed = df_fixed.reindex(
            columns=["Date", "1 Week", "1 Month", "2 Months", "3 Months", "6 Months"]
        ).rename_axis(None, axis=1)

        if path.exists("./data/" + dataset_n + ".csv"):
            df = pd.read_csv("./data/" + dataset_n + ".csv", parse_dates=["Date"])

            df = df.append(df_fixed, ignore_index=True).drop_duplicates()
        else:
            df_hms = pd.read_excel(
                "https://www.norges-bank.no/globalassets/marketdata/hms/data/nibor.xlsx",
                sheet_name="Daily",
                skiprows=6,
                usecols="A,C,E:H",
            )
            df_hms.rename(
                columns={
                    "Unnamed: 0": "Date",
                    "1 week": "1 Week",
                    "1 month": "1 Month",
                    "2 month": "2 Months",
                    "3 month": "3 Months",
                    "6 month": "6 Months",
                },
                inplace=True,
            )
            df_hms = df_hms.loc[
                (df_hms["Date"] > "1986-01-01") & (df_hms["Date"] <= "2013-12-06")
            ].iloc[::-1]

            df = df_fixed.append(df_hms, ignore_index=True)
            df = df.sort_values(by="Date", ignore_index=True)

        write_df(dataset_n, df)
        write_last_updated(dataset_n)
        write_df(dataset_np, df_panel)
        write_last_updated(dataset_np)
    else:
        print("Data already up to date:", dataset_n)


def keyPolicyRate():
    dataset = "no_keyPolicyRate"
    if path.exists("./data/" + dataset + ".csv"):
        df = pd.read_csv("./data/" + dataset + ".csv", parse_dates=["Date"])
        date_last = max(df["Date"]).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(1991, 1, 1).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        url = "https://data.norges-bank.no/api/data/IR/B.KPRA.SD.?format=csv&startPeriod={}&endPeriod={}&locale=en".format(
            delta[1], delta[0]
        )
        res = requests.get(url)

        if res.status_code == 404:
            print("No new rates found for:", dataset)
        else:
            df_new = pd.read_csv(
                url,
                parse_dates=["TIME_PERIOD"],
                delimiter=";",
                thousands=",",
                usecols=["TIME_PERIOD", "OBS_VALUE"],
            )

            df_new.rename(
                columns={"TIME_PERIOD": "Date", "OBS_VALUE": "Rate"}, inplace=True
            )

            df = pd.concat([df, df_new], ignore_index=True)

            write_df(dataset, df)
            write_last_updated(dataset)
    else:
        print("Data already up to date:", dataset)


def nowa():
    dataset = "no_nowa"
    if path.exists("./data/" + dataset + ".csv"):
        df = pd.read_csv("./data/" + dataset + ".csv", parse_dates=["Date"])
        date_last = max(df["Date"]).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(2011, 9, 30).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        url = "https://data.norges-bank.no/api/data/SHORT_RATES/B.NOWA..?format=csv&startPeriod={}&endPeriod={}&locale=en".format(
            delta[1], delta[0]
        )
        res = requests.get(url)

        if res.status_code == 404:
            print("No new rates found for:", dataset)
        else:
            df_new = pd.read_csv(
                url,
                parse_dates=["TIME_PERIOD"],
                delimiter=";",
                thousands=",",
                usecols=[
                    "TIME_PERIOD",
                    "Unit of Measure",
                    "OBS_VALUE",
                    "Calculation Method",
                ],
            )

            df_new.rename(
                columns={
                    "TIME_PERIOD": "Date",
                    "OBS_VALUE": "Value",
                    "Calculation Method": "Qualifier",
                },
                inplace=True,
            )

            qualifier = df_new[["Date", "Qualifier"]].loc[
                df_new["Unit of Measure"] == "Rate"
            ]
            df_pivot = pd.pivot_table(
                df_new, index="Date", columns="Unit of Measure", values="Value"
            )
            df_new = pd.merge(df_pivot, qualifier, how="right", on=["Date"])
            df_new = (
                df_new.reindex(
                    columns=[
                        "Date",
                        "Rate",
                        "Volume",
                        "Qualifier",
                        "Banks lending",
                        "Banks borrowing",
                        "Transactions",
                    ]
                )
                .replace("Alternative method", "Alternative")
                .fillna(0)
            )

            df = pd.concat([df, df_new], ignore_index=True)
            write_df(dataset, df)
            write_last_updated(dataset)
    else:
        print("Data already up to date:", dataset)


def treasuryBills():
    dataset = "no_treasuryBills"
    if path.exists("./data/" + dataset + ".csv"):
        df = pd.read_csv("./data/" + dataset + ".csv", parse_dates=["Date"])
        date_last = max(df["Date"]).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(2003, 1, 8).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        url = "https://data.norges-bank.no/api/data/IR/B.TBIL..?format=csv&startPeriod={}&endPeriod={}&locale=en".format(
            delta[1], delta[0]
        )
        res = requests.get(url)

        if res.status_code == 404:
            print("No new rates found for:", dataset)
        else:
            df_new = pd.read_csv(
                url,
                parse_dates=["TIME_PERIOD"],
                delimiter=";",
                thousands=",",
                usecols=["TIME_PERIOD", "Tenor", "OBS_VALUE"],
            )

            df_new.rename(
                columns={"TIME_PERIOD": "Date", "OBS_VALUE": "Rate"}, inplace=True
            )

            df_new = pd.pivot_table(
                df_new, index="Date", columns="Tenor", values="Rate"
            ).reset_index()
            df_new = df_new.reindex(
                columns=["Date", "3 months", "6 months", "9 months", "12 months"]
            ).rename_axis(None, axis=1)

            df = pd.concat([df, df_new], ignore_index=True)
            write_df(dataset, df)
            write_last_updated(dataset)
    else:
        print("Data already up to date:", dataset)


def governmentBonds():
    dataset = "no_governmentBonds"
    if path.exists("./data/" + dataset + ".csv"):
        df = pd.read_csv("./data/" + dataset + ".csv", parse_dates=["Date"])
        date_last = max(df["Date"]).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(1986, 1, 3).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        url = "https://data.norges-bank.no/api/data/IR/B.GBON..?format=csv&startPeriod={}&endPeriod={}&locale=en".format(
            delta[1], delta[0]
        )
        res = requests.get(url)

        if res.status_code == 404:
            print("No new rates found for:", dataset)
        else:
            df_new = pd.read_csv(
                url,
                parse_dates=["TIME_PERIOD"],
                delimiter=";",
                thousands=",",
                usecols=["TIME_PERIOD", "Tenor", "OBS_VALUE"],
            )

            df_new.rename(
                columns={"TIME_PERIOD": "Date", "OBS_VALUE": "Rate"}, inplace=True
            )

            df_new = pd.pivot_table(
                df_new, index="Date", columns="Tenor", values="Rate"
            ).reset_index()
            df_new = df_new.reindex(
                columns=["Date", "3 years", "5 years", "10 years"]
            ).rename_axis(None, axis=1)

            df = pd.concat([df, df_new], ignore_index=True)

            write_df(dataset, df)
            write_last_updated(dataset)
    else:
        print("Data already up to date:", dataset)


def exchangeRates():
    dataset = "no_exchangeRates"
    if path.exists("./data/" + dataset + ".csv"):
        df = pd.read_csv("./data/" + dataset + ".csv", parse_dates=["Date"])
        date_last = max(df["Date"]).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(1980, 12, 10).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        url = "https://data.norges-bank.no/api/data/EXR/B..NOK.SP?format=csv&startPeriod={}&endPeriod={}&locale=en".format(
            delta[1], delta[0]
        )
        res = requests.get(url)

        if res.status_code == 404:
            print("No new rates found for:", dataset)
        else:
            df_new = pd.read_csv(
                url,
                parse_dates=["TIME_PERIOD"],
                delimiter=";",
                thousands=",",
                usecols=["TIME_PERIOD", "BASE_CUR", "QUOTE_CUR", "OBS_VALUE"],
            )

            df_new.rename(
                columns={
                    "TIME_PERIOD": "Date",
                    "BASE_CUR": "Base Currency",
                    "QUOTE_CUR": "Quote Currency",
                    "OBS_VALUE": "Rate",
                },
                inplace=True,
            )

            df_new = (
                pd.pivot_table(
                    df_new,
                    index=["Date", "Quote Currency"],
                    columns="Base Currency",
                    values="Rate",
                )
                .reset_index()
                .rename_axis(None, axis=1)
            )

            df = pd.concat([df, df_new], ignore_index=True)

            write_df(dataset, df)
            write_last_updated(dataset)
    else:
        print("Data already up to date:", dataset)


def inflation_indicators():
    dataset = "no_cpi"
    file_path = f"./data/{dataset}.csv"
    columns = ["month", "cpi", "cpi_ate", "cpixe", "trimmed_mean", "weighted_median"]

    today = date.today()

    df = (
        pd.read_csv(file_path, parse_dates=["month"])
        if path.exists(file_path)
        else pd.DataFrame(columns=columns)
    )

    last_record_date = df["month"].max() if not df.empty else pd.Timestamp(2005, 12, 1)
    next_update_date = (
        (last_record_date + pd.DateOffset(months=2)).replace(day=10).date()
    )

    if today < next_update_date:
        print(f"Data is up to date. Next update expected on {next_update_date}")
        return

    url = "https://www.norges-bank.no/globalassets/marketdata/ppo/kpi/kpi_tab_en.csv"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return

    df_new = pd.read_csv(StringIO(response.text))
    df_new = df_new.rename(
        columns={
            df_new.columns[0]: "month",
            "CPI": "cpi",
            "CPI-ATE": "cpi_ate",
            "CPIXE": "cpixe",
            "Trimmed mean": "trimmed_mean",
            "Weighted median": "weighted_median",
        }
    )
    df_new["month"] = pd.to_datetime(df_new["month"], format="%b.%y")
    df_new = df_new[df_new["month"] > last_record_date]

    if df_new.empty:
        print("No new data available.")
        return

    df = pd.concat([df, df_new], ignore_index=True) if not df.empty else df_new
    df = df.sort_values("month").reset_index(drop=True)
    df["month"] = df["month"].dt.strftime("%Y-%m")

    write_df(dataset, df)
    write_last_updated(dataset)


if __name__ == "__main__":
    mortgage()
    keyPolicyRate()
    nowa()
    treasuryBills()
    governmentBonds()
    exchangeRates()
    inflation_indicators()
